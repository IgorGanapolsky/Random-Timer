from __future__ import annotations

from scripts import ensure_internal_distribution as eid


class _FakeASCClient:
    def __init__(self):
        self.posts = []

    def get(self, path, params=None):
        if path == "/apps":
            return {"data": [{"id": "app-1"}]}
        if path == "/builds":
            return {
                "data": [
                    {
                        "id": "build-453",
                        "attributes": {"version": "453", "processingState": "VALID"},
                        "relationships": {"preReleaseVersion": {"data": {"id": "prv-1"}}},
                    }
                ],
                "included": [{"id": "prv-1", "type": "preReleaseVersions", "attributes": {"version": "1.3.18"}}],
            }
        raise AssertionError(path)

    def get_all(self, path, params=None):
        if path == "/apps/app-1/betaGroups":
            return [{"id": "group-1", "attributes": {"name": "Internal Testers", "isInternalGroup": True}}]
        if path == "/betaGroups/group-1/builds":
            return [{"id": "build-453"}]
        if path == "/betaGroups/group-1/betaTesters":
            return [{"attributes": {"email": "iganapolsky@gmail.com"}}]
        raise AssertionError(path)

    def request(self, method, path, payload=None, params=None):
        self.posts.append((method, path, payload))
        return {}


def test_ios_internal_distribution_ensures_build_visibility():
    client = _FakeASCClient()
    verifier = eid.TestFlightInternalDistributor(client=client)
    result = verifier.ensure(
        marketing_version="1.3.18",
        groups=["Internal Testers"],
        required_testers=["iganapolsky@gmail.com"],
    )

    assert result["passed"] is True
    assert result["status"] == "VISIBLE"
    assert "build 453" in result["details"]
    assert client.posts == []


def test_ios_internal_distribution_fails_when_required_tester_missing():
    class _MissingTesterClient(_FakeASCClient):
        def get_all(self, path, params=None):
            if path == "/betaGroups/group-1/betaTesters":
                return [{"attributes": {"email": "other@example.com"}}]
            return super().get_all(path, params)

    verifier = eid.TestFlightInternalDistributor(client=_MissingTesterClient())
    result = verifier.ensure(
        marketing_version="1.3.18",
        groups=["Internal Testers"],
        required_testers=["iganapolsky@gmail.com"],
    )

    assert result["passed"] is False
    assert "Required internal TestFlight testers missing" in result["details"]


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.text = "{}"

    def json(self):
        return self._payload


class _FakeRequests:
    def __init__(self):
        self.calls = []

    def request(self, method, url, headers=None, params=None, json=None, timeout=None):
        self.calls.append((method, url, params, json))
        if url.endswith("/releases"):
            return _FakeResponse(
                {
                    "releases": [
                        {
                            "name": "projects/712918404489/apps/1:712918404489:android:abc/releases/rel-1",
                            "displayVersion": "1.3.18",
                            "buildVersion": "557",
                            "createTime": "2026-04-09T12:00:00Z",
                        }
                    ]
                }
            )
        if url.endswith(":distribute"):
            return _FakeResponse({})
        if url.endswith("/testers"):
            return _FakeResponse({"testers": [{"email": "iganapolsky@gmail.com"}]})
        if url.endswith("/groups/internal-testers"):
            return _FakeResponse({"name": "projects/712918404489/groups/internal-testers", "testerCount": 1, "releaseCount": 4})
        raise AssertionError(url)


class _FakeRequestsWithoutProjectTesters(_FakeRequests):
    def request(self, method, url, headers=None, params=None, json=None, timeout=None):
        if url.endswith("/testers"):
            return _FakeResponse({"testers": []})
        return super().request(method, url, headers=headers, params=params, json=json, timeout=timeout)


class _FakeRequestsWithEmptyGroup(_FakeRequests):
    def request(self, method, url, headers=None, params=None, json=None, timeout=None):
        if url.endswith("/groups/internal-testers"):
            return _FakeResponse({"name": "projects/712918404489/groups/internal-testers", "testerCount": 0, "releaseCount": 4})
        return super().request(method, url, headers=headers, params=params, json=json, timeout=timeout)


def _firebase_verifier(fake_requests):
    verifier = eid.FirebaseInternalDistributor(
        app_id="1:712918404489:android:abc",
        service_account_key="{}",
        requests_module=fake_requests,
    )
    verifier._get_token = lambda: "token"
    return verifier


def _ensure_firebase(
    fake_requests,
    *,
    group_aliases=None,
    tester_emails=None,
    required_testers=None,
):
    return _firebase_verifier(fake_requests).ensure(
        build_version="557",
        display_version="1.3.18",
        group_aliases=group_aliases if group_aliases is not None else ["internal-testers"],
        tester_emails=tester_emails if tester_emails is not None else ["iganapolsky@gmail.com"],
        required_testers=required_testers if required_testers is not None else ["iganapolsky@gmail.com"],
    )


def test_firebase_internal_distribution_distributes_and_verifies():
    fake_requests = _FakeRequests()
    result = _ensure_firebase(fake_requests)

    assert result["passed"] is True
    assert result["status"] == "VISIBLE"
    assert "internal-testers" in result["details"]
    assert any(call[1].endswith(":distribute") for call in fake_requests.calls)


def test_firebase_internal_distribution_allows_project_tester_list_propagation_delay():
    result = _ensure_firebase(_FakeRequestsWithoutProjectTesters())

    assert result["passed"] is True
    assert result["status"] == "VISIBLE"
    assert "project tester list pending" in result["details"]
    assert "direct tester distribution accepted for 1 tester" in result["details"]


def test_firebase_internal_distribution_allows_empty_group_when_direct_tester_delivery_succeeded():
    result = _ensure_firebase(_FakeRequestsWithEmptyGroup())

    assert result["passed"] is True
    assert result["status"] == "VISIBLE"
    assert "group warnings: Firebase group 'internal-testers' has no testers" in result["details"]
    assert "direct tester distribution accepted for 1 tester" in result["details"]


def test_firebase_internal_distribution_fails_when_required_tester_not_distributed_or_visible():
    result = _ensure_firebase(
        _FakeRequestsWithoutProjectTesters(),
        tester_emails=["other@example.com"],
        required_testers=["iganapolsky@gmail.com"],
    )

    assert result["passed"] is False
    assert "not included in direct distribution" in result["details"]


def test_firebase_internal_distribution_fails_without_visibility_targets():
    result = _ensure_firebase(
        _FakeRequests(),
        group_aliases=[],
        tester_emails=[],
        required_testers=[],
    )

    assert result["passed"] is False
    assert "no tester emails or group aliases" in result["details"]
