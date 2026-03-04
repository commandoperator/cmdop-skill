from __future__ import annotations

import httpx

from .models import (
    PaginatedSkillListList,
    PaginatedSkillReviewList,
    PatchedSkillUpdateRequest,
    SkillCategory,
    SkillCreate,
    SkillCreateRequest,
    SkillDetail,
    SkillInstall,
    SkillListRequest,
    SkillPublishRequest,
    SkillStar,
    SkillTag,
    SkillUpdate,
    SkillUpdateRequest,
    SkillUploadCoverRequestRequest,
    SkillUploadCoverResponse,
    SkillVersion,
)


class SyncSkillsSkillsAPI:
    """Synchronous API endpoints for Skills."""

    def __init__(self, client: httpx.Client):
        """Initialize sync sub-client with shared httpx client."""
        self._client = client

    def categories_list(
        self,
        ordering: str | None = None,
        search: str | None = None,
    ) -> list[SkillCategory]:
        """
        List skill categories

        ViewSet for SkillCategory - read-only, public access.
        """
        url = "/api/skills/categories/"
        _params = {
            k: v for k, v in {
                "ordering": ordering,
                "search": search,
            }.items() if v is not None
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return [SkillCategory.model_validate(item) for item in response.json()]


    def categories_retrieve(self, slug: str) -> SkillCategory:
        """
        Get category details

        ViewSet for SkillCategory - read-only, public access.
        """
        url = f"/api/skills/categories/{slug}/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillCategory.model_validate(response.json())


    def skills_list(
        self,
        category: str | None = None,
        lang: str | None = None,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
        tag: str | None = None,
    ) -> list[PaginatedSkillListList]:
        """
        List published skills

        List public, published skills. Filterable by category, tag, search.
        """
        url = "/api/skills/skills/"
        _params = {
            k: v for k, v in {
                "category": category,
                "lang": lang,
                "ordering": ordering,
                "page": page,
                "page_size": page_size,
                "search": search,
                "tag": tag,
            }.items() if v is not None
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedSkillListList.model_validate(response.json())


    def skills_create(self, data: SkillCreateRequest) -> SkillCreate:
        """
        Create a new skill

        ViewSet for Skill CRUD and marketplace operations. Public endpoints:
        list, retrieve Authenticated: create, update, delete, star, install, my,
        versions, publish Admin: verify, suspend
        """
        url = "/api/skills/skills/"
        response = self._client.post(url, json=data.model_dump(mode="json", exclude_unset=True, exclude_none=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillCreate.model_validate(response.json())


    def skills_retrieve(self, slug: str, lang: str | None = None) -> SkillDetail:
        """
        Get skill details

        ViewSet for Skill CRUD and marketplace operations. Public endpoints:
        list, retrieve Authenticated: create, update, delete, star, install, my,
        versions, publish Admin: verify, suspend
        """
        url = f"/api/skills/skills/{slug}/"
        _params = {
            k: v for k, v in {
                "lang": lang,
            }.items() if v is not None
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillDetail.model_validate(response.json())


    def skills_update(self, slug: str, data: SkillUpdateRequest) -> SkillUpdate:
        """
        Update a skill

        ViewSet for Skill CRUD and marketplace operations. Public endpoints:
        list, retrieve Authenticated: create, update, delete, star, install, my,
        versions, publish Admin: verify, suspend
        """
        url = f"/api/skills/skills/{slug}/"
        # Build multipart form data
        _files = {}
        _form_data = {}
        _raw_data = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if 'icon' in _raw_data and _raw_data['icon'] is not None:
            _files['icon'] = _raw_data['icon']
        if 'cover' in _raw_data and _raw_data['cover'] is not None:
            _files['cover'] = _raw_data['cover']
        if 'name' in _raw_data and _raw_data['name'] is not None:
            _form_data['name'] = _raw_data['name']
        if 'category' in _raw_data and _raw_data['category'] is not None:
            _val = _raw_data['category']
            _form_data['category'] = _val.value if hasattr(_val, 'value') else _val
        if 'visibility' in _raw_data and _raw_data['visibility'] is not None:
            _val = _raw_data['visibility']
            _form_data['visibility'] = _val.value if hasattr(_val, 'value') else _val
        if 'status' in _raw_data and _raw_data['status'] is not None:
            _val = _raw_data['status']
            _form_data['status'] = _val.value if hasattr(_val, 'value') else _val
        if 'repository_url' in _raw_data and _raw_data['repository_url'] is not None:
            _form_data['repository_url'] = _raw_data['repository_url']
        response = self._client.put(url, files=_files if _files else None, data=_form_data if _form_data else None)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillUpdate.model_validate(response.json())


    def skills_partial_update(
        self,
        slug: str,
        data: PatchedSkillUpdateRequest | None = None,
    ) -> SkillUpdate:
        """
        Partially update a skill

        ViewSet for Skill CRUD and marketplace operations. Public endpoints:
        list, retrieve Authenticated: create, update, delete, star, install, my,
        versions, publish Admin: verify, suspend
        """
        url = f"/api/skills/skills/{slug}/"
        _json = data.model_dump(mode="json", exclude_unset=True, exclude_none=True) if data else None
        response = self._client.patch(url, json=_json)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillUpdate.model_validate(response.json())


    def skills_destroy(self, slug: str) -> None:
        """
        Delete a skill

        ViewSet for Skill CRUD and marketplace operations. Public endpoints:
        list, retrieve Authenticated: create, update, delete, star, install, my,
        versions, publish Admin: verify, suspend
        """
        url = f"/api/skills/skills/{slug}/"
        response = self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def skills_install_create(self, slug: str) -> SkillInstall:
        """
        Install a skill

        Record an install and return install command + README.
        """
        url = f"/api/skills/skills/{slug}/install/"
        response = self._client.post(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillInstall.model_validate(response.json())


    def skills_publish_create(self, slug: str, data: SkillPublishRequest) -> None:
        """
        Publish a new skill version (async)

        Upload raw manifest — starts background LLM parsing + translation.
        Returns 202 immediately. Poll /publish-status/ for result.
        """
        url = f"/api/skills/skills/{slug}/publish/"
        response = self._client.post(url, json=data.model_dump(mode="json", exclude_unset=True, exclude_none=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def skills_publish_status_retrieve(self, slug: str) -> None:
        """
        Check publish status

        Poll this endpoint after POST /publish/ to check progress.
        """
        url = f"/api/skills/skills/{slug}/publish-status/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def skills_reviews_list(
        self,
        slug: str,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedSkillReviewList]:
        """
        List reviews for a skill

        Paginated list of visible reviews for a skill, ordered by newest first.
        """
        url = f"/api/skills/skills/{slug}/reviews/"
        _params = {
            k: v for k, v in {
                "ordering": ordering,
                "page": page,
                "page_size": page_size,
                "search": search,
            }.items() if v is not None
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedSkillReviewList.model_validate(response.json())


    def skills_star_create(self, slug: str) -> SkillStar:
        """
        Toggle star on a skill

        Star or unstar a skill. Returns new state.
        """
        url = f"/api/skills/skills/{slug}/star/"
        response = self._client.post(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillStar.model_validate(response.json())


    def skills_suspend_create(self, slug: str, data: SkillListRequest) -> None:
        """
        Suspend a skill (admin only)

        Suspend a skill.
        """
        url = f"/api/skills/skills/{slug}/suspend/"
        # Build multipart form data
        _files = {}
        _form_data = {}
        _raw_data = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if 'icon' in _raw_data and _raw_data['icon'] is not None:
            _files['icon'] = _raw_data['icon']
        if 'cover' in _raw_data and _raw_data['cover'] is not None:
            _files['cover'] = _raw_data['cover']
        if 'name' in _raw_data and _raw_data['name'] is not None:
            _form_data['name'] = _raw_data['name']
        if 'category' in _raw_data and _raw_data['category'] is not None:
            _form_data['category'] = _raw_data['category']
        if 'visibility' in _raw_data and _raw_data['visibility'] is not None:
            _val = _raw_data['visibility']
            _form_data['visibility'] = _val.value if hasattr(_val, 'value') else _val
        if 'status' in _raw_data and _raw_data['status'] is not None:
            _val = _raw_data['status']
            _form_data['status'] = _val.value if hasattr(_val, 'value') else _val
        response = self._client.post(url, files=_files if _files else None, data=_form_data if _form_data else None)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def skills_upload_cover_create(
        self,
        slug: str,
        data: SkillUploadCoverRequestRequest,
    ) -> None:
        """
        Upload or delete cover image

        POST: Upload/replace cover image. DELETE: Remove cover. Only the author
        can do this.
        """
        url = f"/api/skills/skills/{slug}/upload-cover/"
        # Build multipart form data
        _files = {}
        _form_data = {}
        _raw_data = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if 'cover' in _raw_data and _raw_data['cover'] is not None:
            _files['cover'] = _raw_data['cover']
        response = self._client.post(url, files=_files if _files else None, data=_form_data if _form_data else None)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def skills_upload_cover_destroy(self, slug: str) -> None:
        """
        Upload or delete cover image

        POST: Upload/replace cover image. DELETE: Remove cover. Only the author
        can do this.
        """
        url = f"/api/skills/skills/{slug}/upload-cover/"
        response = self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def skills_verify_create(self, slug: str, data: SkillListRequest) -> None:
        """
        Toggle skill verification (admin only)

        Toggle is_verified on a skill.
        """
        url = f"/api/skills/skills/{slug}/verify/"
        # Build multipart form data
        _files = {}
        _form_data = {}
        _raw_data = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if 'icon' in _raw_data and _raw_data['icon'] is not None:
            _files['icon'] = _raw_data['icon']
        if 'cover' in _raw_data and _raw_data['cover'] is not None:
            _files['cover'] = _raw_data['cover']
        if 'name' in _raw_data and _raw_data['name'] is not None:
            _form_data['name'] = _raw_data['name']
        if 'category' in _raw_data and _raw_data['category'] is not None:
            _form_data['category'] = _raw_data['category']
        if 'visibility' in _raw_data and _raw_data['visibility'] is not None:
            _val = _raw_data['visibility']
            _form_data['visibility'] = _val.value if hasattr(_val, 'value') else _val
        if 'status' in _raw_data and _raw_data['status'] is not None:
            _val = _raw_data['status']
            _form_data['status'] = _val.value if hasattr(_val, 'value') else _val
        response = self._client.post(url, files=_files if _files else None, data=_form_data if _form_data else None)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )


    def skills_versions_list(
        self,
        slug: str,
        ordering: str | None = None,
        search: str | None = None,
    ) -> list[SkillVersion]:
        """
        List skill versions

        Get all versions of a skill.
        """
        url = f"/api/skills/skills/{slug}/versions/"
        _params = {
            k: v for k, v in {
                "ordering": ordering,
                "search": search,
            }.items() if v is not None
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return [SkillVersion.model_validate(item) for item in response.json()]


    def skills_my_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedSkillListList]:
        """
        List current user's skills

        Returns all skills authored by the current user, including private and
        draft.
        """
        url = "/api/skills/skills/my/"
        _params = {
            k: v for k, v in {
                "ordering": ordering,
                "page": page,
                "page_size": page_size,
                "search": search,
            }.items() if v is not None
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedSkillListList.model_validate(response.json())


    def tags_list(
        self,
        ordering: str | None = None,
        search: str | None = None,
    ) -> list[SkillTag]:
        """
        List skill tags

        ViewSet for SkillTag - read-only, public access.
        """
        url = "/api/skills/tags/"
        _params = {
            k: v for k, v in {
                "ordering": ordering,
                "search": search,
            }.items() if v is not None
        }
        response = self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return [SkillTag.model_validate(item) for item in response.json()]


    def tags_retrieve(self, slug: str) -> SkillTag:
        """
        Get tag details

        ViewSet for SkillTag - read-only, public access.
        """
        url = f"/api/skills/tags/{slug}/"
        response = self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return SkillTag.model_validate(response.json())


