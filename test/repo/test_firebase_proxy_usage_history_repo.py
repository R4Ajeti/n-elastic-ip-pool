import base64
import json
import unittest

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    FIREBASE_DATABASE_TYPE_ENV_NAME_STR,
    FIREBASE_DATABASE_TYPE_FIRESTORE_STR,
    FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR,
    FIREBASE_FIRESTORE_KEY_BASE64_ENV_NAME_STR,
    FIREBASE_REALTIME_DATABASE_KEY_BASE64_ENV_NAME_STR,
    FIREBASE_REALTIME_DATABASE_URL_ENV_NAME_STR,
)
from n_elastic_ip_pool.repo.firebase_proxy_usage_history_repo import (
    FirebaseProxyUsageHistoryRepo,
)


def encodeCredentialDict(credentialDict: dict) -> str:
    return base64.b64encode(json.dumps(credentialDict).encode("utf-8")).decode("utf-8")


class FakeFirestoreSnapshot:
    def __init__(self, dataDict: dict | None) -> None:
        self.dataDict = dataDict
        self.exists = dataDict is not None

    def to_dict(self) -> dict | None:
        if self.dataDict is None:
            return None

        return dict(self.dataDict)


class FakeFirestoreHistoryCollection:
    def __init__(self, document) -> None:
        self.document = document

    def add(self, recordDict: dict) -> None:
        self.document.historyList.append(dict(recordDict))


class FakeFirestoreDocument:
    def __init__(self) -> None:
        self.dataDict: dict | None = None
        self.historyList: list[dict] = []

    def get(self) -> FakeFirestoreSnapshot:
        return FakeFirestoreSnapshot(self.dataDict)

    def set(self, dataDict: dict, merge: bool = False) -> None:
        if merge and self.dataDict:
            self.dataDict.update(dataDict)
            return None

        self.dataDict = dict(dataDict)
        return None

    def collection(self, collectionNameStr: str) -> FakeFirestoreHistoryCollection:
        self.historyCollectionNameStr = collectionNameStr
        return FakeFirestoreHistoryCollection(self)


class FakeFirestoreCollection:
    def __init__(self) -> None:
        self.documentByIdDict: dict[str, FakeFirestoreDocument] = {}

    def document(self, documentIdStr: str) -> FakeFirestoreDocument:
        if documentIdStr not in self.documentByIdDict:
            self.documentByIdDict[documentIdStr] = FakeFirestoreDocument()

        return self.documentByIdDict[documentIdStr]


class FakeFirestoreClient:
    def __init__(self) -> None:
        self.collectionByNameDict: dict[str, FakeFirestoreCollection] = {}

    def collection(self, collectionNameStr: str) -> FakeFirestoreCollection:
        if collectionNameStr not in self.collectionByNameDict:
            self.collectionByNameDict[collectionNameStr] = FakeFirestoreCollection()

        return self.collectionByNameDict[collectionNameStr]


class FakeRealtimeReference:
    def __init__(self, rootDict: dict | None = None, pathTuple: tuple[str, ...] = ()) -> None:
        self.rootDict = rootDict if rootDict is not None else {}
        self.pathTuple = pathTuple

    def child(self, pathStr: str):
        return FakeRealtimeReference(self.rootDict, (*self.pathTuple, pathStr))

    def get(self):
        return self.getNode(createBool=False)

    def update(self, dataDict: dict) -> None:
        nodeDict = self.getNode(createBool=True)
        nodeDict.update(dataDict)

    def push(self):
        nodeDict = self.getNode(createBool=True)
        itemKeyStr = f"item_{len(nodeDict)}"
        return self.child(itemKeyStr)

    def set(self, dataDict: dict) -> None:
        parentRef = FakeRealtimeReference(self.rootDict, self.pathTuple[:-1])
        parentDict = parentRef.getNode(createBool=True)
        parentDict[self.pathTuple[-1]] = dict(dataDict)

    def getNode(self, createBool: bool):
        nodeValue = self.rootDict
        for pathPartStr in self.pathTuple:
            if not isinstance(nodeValue, dict):
                return None

            if pathPartStr not in nodeValue:
                if not createBool:
                    return None
                nodeValue[pathPartStr] = {}

            nodeValue = nodeValue[pathPartStr]

        return nodeValue


class FirebaseProxyUsageHistoryRepoTest(unittest.TestCase):
    def testRepoChoosesFirestoreWhenConfigured(self) -> None:
        credentialDict = {"project_id": "sample-project"}
        client = FakeFirestoreClient()
        capturedCredentialList = []

        def buildClient(inputCredentialDict: dict):
            capturedCredentialList.append(inputCredentialDict)
            return client

        repo = FirebaseProxyUsageHistoryRepo(
            envDict={
                FIREBASE_DATABASE_TYPE_ENV_NAME_STR: FIREBASE_DATABASE_TYPE_FIRESTORE_STR,
                FIREBASE_FIRESTORE_KEY_BASE64_ENV_NAME_STR: encodeCredentialDict(
                    credentialDict,
                ),
            },
            firestoreClientFactory=buildClient,
        )

        resultDict = repo.recordProxyUsage(
            "proxy-one.example.net:8080",
            {"source": "unit_test"},
        )

        self.assertTrue(repo.getStorageStatus()["enabled"])
        self.assertEqual(repo.databaseTypeStr, FIREBASE_DATABASE_TYPE_FIRESTORE_STR)
        self.assertEqual(capturedCredentialList, [credentialDict])
        self.assertEqual(resultDict["usage_count"], 1)
        self.assertEqual(repo.getProxyUsageCount("proxy-one.example.net:8080"), 1)

    def testRepoChoosesRealtimeDatabaseWhenConfigured(self) -> None:
        credentialDict = {"project_id": "sample-project"}
        rootRef = FakeRealtimeReference()
        capturedConfigList = []

        def buildReference(inputCredentialDict: dict, databaseUrlStr: str):
            capturedConfigList.append((inputCredentialDict, databaseUrlStr))
            return rootRef

        repo = FirebaseProxyUsageHistoryRepo(
            envDict={
                FIREBASE_DATABASE_TYPE_ENV_NAME_STR: (
                    FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR
                ),
                FIREBASE_REALTIME_DATABASE_KEY_BASE64_ENV_NAME_STR: encodeCredentialDict(
                    credentialDict,
                ),
                FIREBASE_REALTIME_DATABASE_URL_ENV_NAME_STR: (
                    "https://sample-project.firebaseio.com"
                ),
            },
            realtimeDatabaseReferenceFactory=buildReference,
        )

        resultDict = repo.recordProxyUsage(
            "proxy-two.example.net:8080",
            {"source": "unit_test"},
        )

        self.assertTrue(repo.getStorageStatus()["enabled"])
        self.assertEqual(
            repo.databaseTypeStr,
            FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR,
        )
        self.assertEqual(
            capturedConfigList,
            [(credentialDict, "https://sample-project.firebaseio.com")],
        )
        self.assertEqual(resultDict["usage_count"], 1)
        self.assertEqual(repo.getProxyUsageCount("proxy-two.example.net:8080"), 1)

    def testMissingFirebaseEnvironmentUsesFallbackStorage(self) -> None:
        repo = FirebaseProxyUsageHistoryRepo(envDict={})

        resultDict = repo.recordProxyUsage(
            "203.0.113.10:8080",
            {"source": "unit_test"},
        )
        disabledDict = repo.markProxyDisabled("203.0.113.10:8080")

        self.assertFalse(repo.getStorageStatus()["enabled"])
        self.assertEqual(resultDict["usage_count"], 1)
        self.assertTrue(disabledDict["disabled"])
        self.assertTrue(repo.isProxyDisabled("203.0.113.10:8080"))

    def testInvalidFirebaseCredentialUsesFallbackStorage(self) -> None:
        repo = FirebaseProxyUsageHistoryRepo(
            envDict={
                FIREBASE_DATABASE_TYPE_ENV_NAME_STR: FIREBASE_DATABASE_TYPE_FIRESTORE_STR,
                FIREBASE_FIRESTORE_KEY_BASE64_ENV_NAME_STR: "not-valid-base64",
            },
        )

        resultDict = repo.recordProxyUsage("proxy-one.example.net:8080")

        self.assertFalse(repo.getStorageStatus()["enabled"])
        self.assertEqual(repo.getStorageStatus()["status"], "invalid_credential")
        self.assertEqual(resultDict["usage_count"], 1)


if __name__ == "__main__":
    unittest.main()
