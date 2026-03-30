"""Mattermost 로그인/이미지 다운로드 모듈"""
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

KST = timezone(timedelta(hours=9))


class MattermostImageFetcher:
    """Mattermost 채널에서 10층 식단 이미지를 수집하는 클래스"""

    def __init__(self):
        self.base_url = os.environ["MATTERMOST_BASE_URL"].rstrip("/")
        self.channel_id = os.environ["MATTERMOST_CHANNEL_ID"]
        login_json = os.environ["MM_LOGIN_JSON"]
        self.login_data = json.loads(login_json)
        self.token: Optional[str] = None
        self.session = requests.Session()

    def login(self) -> None:
        """Mattermost 로그인 후 토큰 저장"""
        resp = self.session.post(
            f"{self.base_url}/api/v4/users/login",
            json=self.login_data,
            timeout=30,
        )
        resp.raise_for_status()
        self.token = resp.headers.get("Token")
        if not self.token:
            raise ValueError("로그인 응답에서 Token을 찾을 수 없습니다.")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        print("✓ Mattermost 로그인 성공")

    def _get_recent_posts(self, per_page: int = 60) -> list:
        """채널의 최신 게시글 목록 반환"""
        resp = self.session.get(
            f"{self.base_url}/api/v4/channels/{self.channel_id}/posts",
            params={"per_page": per_page},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        order = data.get("order", [])
        posts = data.get("posts", {})
        return [posts[pid] for pid in order if pid in posts]

    def _is_image_file(self, filename: str) -> bool:
        """이미지 파일 여부 확인 (png/jpg/jpeg)"""
        return filename.lower().rsplit(".", 1)[-1] in {"png", "jpg", "jpeg"}

    def _is_post_this_week(self, post: dict) -> bool:
        """게시글 업로드 시각(create_at)이 이번 주(월~금, KST 기준)인지 확인"""
        create_at_ms = post.get("create_at", 0)
        post_date = datetime.fromtimestamp(create_at_ms / 1000, tz=KST)
        today = datetime.now(KST)
        days_since_monday = today.weekday()
        monday = (today - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        friday = (monday + timedelta(days=4)).replace(hour=23, minute=59, second=59, microsecond=999999)
        return monday <= post_date <= friday

    def _get_file_info(self, file_id: str) -> dict:
        """파일 메타데이터 조회"""
        resp = self.session.get(
            f"{self.base_url}/api/v4/files/{file_id}/info",
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _download_file(self, file_id: str, dest_path: str) -> None:
        """파일 다운로드"""
        resp = self.session.get(
            f"{self.base_url}/api/v4/files/{file_id}",
            timeout=60,
            stream=True,
        )
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

    def fetch_floor10_image(self, dest_dir: Optional[str] = None) -> str:
        """
        채널에서 10층 식단 이미지를 찾아 다운로드

        Args:
            dest_dir: 저장 디렉토리. None이면 임시 디렉토리 사용

        Returns:
            다운로드된 이미지 파일 경로

        Raises:
            RuntimeError: 이미지를 찾을 수 없거나 다운로드 실패 시
        """
        self.login()
        posts = self._get_recent_posts()

        # 이미지가 첨부된 게시글 순회 (최신 순)
        for post in posts:
            file_ids = post.get("file_ids") or []
            post_message = post.get("message", "")

            if not self._is_post_this_week(post):
                print(f"⏭️  이번 주 게시글이 아님, 건너뜀 (create_at: {post.get('create_at')})")
                continue

            for file_id in file_ids:
                try:
                    info = self._get_file_info(file_id)
                except Exception:
                    continue

                filename = info.get("name", "")
                if not self._is_image_file(filename):
                    continue

                # 파일명이나 게시글 본문에서 10층/공존 키워드 확인
                combined = (filename + post_message).lower()
                is_floor10 = any(kw in combined for kw in ["10층", "10f", "공존"])

                if is_floor10:
                    save_dir = dest_dir or tempfile.gettempdir()
                    os.makedirs(save_dir, exist_ok=True)
                    dest_path = os.path.join(save_dir, filename)
                    self._download_file(file_id, dest_path)
                    print(f"✓ 10층 식단 이미지 다운로드: {dest_path}")
                    return dest_path

        # 키워드 매칭 실패 시 이번 주 최신 이미지로 fallback
        for post in posts:
            file_ids = post.get("file_ids") or []

            if not self._is_post_this_week(post):
                continue

            for file_id in file_ids:
                try:
                    info = self._get_file_info(file_id)
                except Exception:
                    continue

                filename = info.get("name", "")
                if not self._is_image_file(filename):
                    continue

                save_dir = dest_dir or tempfile.gettempdir()
                os.makedirs(save_dir, exist_ok=True)
                dest_path = os.path.join(save_dir, filename)
                self._download_file(file_id, dest_path)
                print(f"⚠️  10층 키워드 미확인, 최신 이미지 사용: {dest_path}")
                return dest_path

        raise RuntimeError("채널에서 이미지를 찾을 수 없습니다.")
