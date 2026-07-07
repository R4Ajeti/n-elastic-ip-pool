import importlib
import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from n_elastic_ip_pool.constant.elastic_ip_pool_constant import (
    DEFAULT_FIREBASE_COLLECTION_NAME_STR,
    DEFAULT_FIREBASE_USAGE_HISTORY_PATH_STR,
    FIREBASE_DATABASE_TYPE_ENV_NAME_STR,
    FIREBASE_DATABASE_TYPE_FIRESTORE_STR,
    FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR,
    FIREBASE_FIRESTORE_KEY_BASE64_ENV_NAME_STR,
    FIREBASE_REALTIME_DATABASE_KEY_BASE64_ENV_NAME_STR,
    FIREBASE_REALTIME_DATABASE_URL_ENV_NAME_STR,
)
from n_elastic_ip_pool.helper.base64_json_helper import decodeBase64JsonObject
from n_elastic_ip_pool.helper.string_hash_helper import hashStringValue


class FirebaseProxyUsageHistoryRepo:
    """Optional Firebase storage for proxy usage counts and history.

    Credential env values are base64-encoded JSON objects. The JSON may be a
    Firebase service-account object or another Firebase credential payload that
    the injected client factory understands.
    """

    def __init__(
        self,
        envDict: Mapping[str, str] | None = None,
        firestoreClientFactory: Callable[[dict], object] | None = None,
        realtimeDatabaseReferenceFactory: Callable[[dict, str], object] | None = None,
        collectionNameStr: str = DEFAULT_FIREBASE_COLLECTION_NAME_STR,
        usageHistoryPathStr: str = DEFAULT_FIREBASE_USAGE_HISTORY_PATH_STR,
        appNameStr: str = "n_elastic_ip_pool_proxy_usage_history",
    ) -> None:
        self.envDict = envDict if envDict is not None else os.environ
        self.firestoreClientFactory = firestoreClientFactory
        self.realtimeDatabaseReferenceFactory = realtimeDatabaseReferenceFactory
        self.collectionNameStr = collectionNameStr or DEFAULT_FIREBASE_COLLECTION_NAME_STR
        self.usageHistoryPathStr = self.normalizePathStr(
            usageHistoryPathStr or DEFAULT_FIREBASE_USAGE_HISTORY_PATH_STR,
        )
        self.appNameStr = appNameStr
        self.databaseTypeStr = self.normalizeDatabaseTypeStr(
            self.envDict.get(FIREBASE_DATABASE_TYPE_ENV_NAME_STR, ""),
        )
        self.storageEnabledBool = False
        self.storageStatusStr = "not_configured"
        self.storageErrorStr = ""
        self.firestoreClient = None
        self.realtimeDatabaseReference = None
        self.fallbackUsageStateByProxyIdDict: dict[str, dict] = {}
        self.fallbackUsageHistoryList: list[dict] = []

        self.initializeStorage()

    def initializeStorage(self) -> None:
        if self.databaseTypeStr == FIREBASE_DATABASE_TYPE_FIRESTORE_STR:
            self.initializeFirestoreStorage()
            return None

        if self.databaseTypeStr == FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR:
            self.initializeRealtimeDatabaseStorage()
            return None

        self.storageStatusStr = "not_configured"
        return None

    def initializeFirestoreStorage(self) -> None:
        encodedCredentialStr = self.envDict.get(
            FIREBASE_FIRESTORE_KEY_BASE64_ENV_NAME_STR,
            "",
        )
        credentialDict = decodeBase64JsonObject(encodedCredentialStr)
        if credentialDict is None:
            self.storageStatusStr = (
                "invalid_credential" if encodedCredentialStr else "missing_credential"
            )
            return None

        try:
            if self.firestoreClientFactory:
                self.firestoreClient = self.firestoreClientFactory(credentialDict)
            else:
                self.firestoreClient = self.buildFirestoreClient(credentialDict)
        except Exception as error:
            self.storageStatusStr = "firebase_initialization_failed"
            self.storageErrorStr = error.__class__.__name__
            self.firestoreClient = None
            return None

        self.storageEnabledBool = self.firestoreClient is not None
        self.storageStatusStr = "enabled" if self.storageEnabledBool else "not_configured"
        return None

    def initializeRealtimeDatabaseStorage(self) -> None:
        encodedCredentialStr = self.envDict.get(
            FIREBASE_REALTIME_DATABASE_KEY_BASE64_ENV_NAME_STR,
            "",
        )
        databaseUrlStr = self.envDict.get(FIREBASE_REALTIME_DATABASE_URL_ENV_NAME_STR, "")
        credentialDict = decodeBase64JsonObject(encodedCredentialStr)
        if credentialDict is None:
            self.storageStatusStr = (
                "invalid_credential" if encodedCredentialStr else "missing_credential"
            )
            return None

        if not databaseUrlStr:
            self.storageStatusStr = "missing_database_url"
            return None

        try:
            if self.realtimeDatabaseReferenceFactory:
                self.realtimeDatabaseReference = self.realtimeDatabaseReferenceFactory(
                    credentialDict,
                    databaseUrlStr,
                )
            else:
                self.realtimeDatabaseReference = self.buildRealtimeDatabaseReference(
                    credentialDict,
                    databaseUrlStr,
                )
        except Exception as error:
            self.storageStatusStr = "firebase_initialization_failed"
            self.storageErrorStr = error.__class__.__name__
            self.realtimeDatabaseReference = None
            return None

        self.storageEnabledBool = self.realtimeDatabaseReference is not None
        self.storageStatusStr = "enabled" if self.storageEnabledBool else "not_configured"
        return None

    def buildFirestoreClient(self, credentialDict: dict):
        firebaseAdmin = importlib.import_module("firebase_admin")
        credentialsModule = importlib.import_module("firebase_admin.credentials")
        firestoreModule = importlib.import_module("firebase_admin.firestore")
        app = self.initializeFirebaseApp(
            firebaseAdmin,
            credentialsModule,
            credentialDict,
            {},
        )
        return firestoreModule.client(app=app)

    def buildRealtimeDatabaseReference(self, credentialDict: dict, databaseUrlStr: str):
        firebaseAdmin = importlib.import_module("firebase_admin")
        credentialsModule = importlib.import_module("firebase_admin.credentials")
        databaseModule = importlib.import_module("firebase_admin.db")
        app = self.initializeFirebaseApp(
            firebaseAdmin,
            credentialsModule,
            credentialDict,
            {"databaseURL": databaseUrlStr},
        )
        return databaseModule.reference("/", app=app)

    def initializeFirebaseApp(
        self,
        firebaseAdmin,
        credentialsModule,
        credentialDict: dict,
        optionsDict: dict,
    ):
        try:
            return firebaseAdmin.get_app(self.appNameStr)
        except ValueError:
            credential = credentialsModule.Certificate(credentialDict)
            return firebaseAdmin.initialize_app(
                credential,
                optionsDict,
                name=self.appNameStr,
            )

    def getStorageStatus(self) -> dict:
        return {
            "enabled": self.storageEnabledBool,
            "database_type": self.databaseTypeStr,
            "status": self.storageStatusStr,
            "error": self.storageErrorStr,
        }

    def getProxyUsageCount(self, proxyStr: str) -> int:
        return int(self.getProxyUsageState(proxyStr).get("usage_count") or 0)

    def isProxyDisabled(self, proxyStr: str) -> bool:
        return bool(self.getProxyUsageState(proxyStr).get("disabled"))

    def getProxyUsageState(self, proxyStr: str) -> dict:
        if self.isFirestoreEnabled():
            try:
                return self.normalizeProxyUsageStateDict(
                    proxyStr,
                    self.getFirestoreProxyStateDict(proxyStr),
                )
            except Exception as error:
                self.recordStorageError(error)

        if self.isRealtimeDatabaseEnabled():
            try:
                return self.normalizeProxyUsageStateDict(
                    proxyStr,
                    self.getRealtimeDatabaseProxyStateDict(proxyStr),
                )
            except Exception as error:
                self.recordStorageError(error)

        return self.normalizeProxyUsageStateDict(
            proxyStr,
            self.getFallbackProxyStateDict(proxyStr),
        )

    def recordProxyUsage(
        self,
        proxyStr: str,
        usageRecordDict: dict | None = None,
    ) -> dict:
        normalizedRecordDict = self.buildUsageRecordDict(proxyStr, usageRecordDict)
        if self.isFirestoreEnabled():
            try:
                return self.recordFirestoreProxyUsage(proxyStr, normalizedRecordDict)
            except Exception as error:
                self.recordStorageError(error)

        if self.isRealtimeDatabaseEnabled():
            try:
                return self.recordRealtimeDatabaseProxyUsage(proxyStr, normalizedRecordDict)
            except Exception as error:
                self.recordStorageError(error)

        return self.recordFallbackProxyUsage(proxyStr, normalizedRecordDict)

    def markProxyDisabled(self, proxyStr: str) -> dict:
        if self.isFirestoreEnabled():
            try:
                return self.markFirestoreProxyDisabled(proxyStr)
            except Exception as error:
                self.recordStorageError(error)

        if self.isRealtimeDatabaseEnabled():
            try:
                return self.markRealtimeDatabaseProxyDisabled(proxyStr)
            except Exception as error:
                self.recordStorageError(error)

        return self.markFallbackProxyDisabled(proxyStr)

    def getFirestoreProxyStateDict(self, proxyStr: str) -> dict:
        documentRef = self.getFirestoreProxyDocumentRef(proxyStr)
        snapshot = documentRef.get()
        if not getattr(snapshot, "exists", True):
            return {}

        stateDict = snapshot.to_dict()
        if isinstance(stateDict, dict):
            return stateDict

        return {}

    def recordFirestoreProxyUsage(self, proxyStr: str, usageRecordDict: dict) -> dict:
        documentRef = self.getFirestoreProxyDocumentRef(proxyStr)
        currentStateDict = self.getFirestoreProxyStateDict(proxyStr)
        usageCountInt = self.getUsageCountInt(currentStateDict) + 1
        disabledBool = bool(currentStateDict.get("disabled"))
        usedAtStr = str(usageRecordDict.get("used_at") or self.getCurrentTimeStr())
        stateDict = {
            "proxy": proxyStr,
            "usage_count": usageCountInt,
            "disabled": disabledBool,
            "updated_at": usedAtStr,
        }
        documentRef.set(stateDict, merge=True)
        documentRef.collection("history").add(usageRecordDict)
        return self.normalizeProxyUsageStateDict(proxyStr, stateDict)

    def markFirestoreProxyDisabled(self, proxyStr: str) -> dict:
        documentRef = self.getFirestoreProxyDocumentRef(proxyStr)
        currentStateDict = self.getFirestoreProxyStateDict(proxyStr)
        stateDict = {
            "proxy": proxyStr,
            "usage_count": self.getUsageCountInt(currentStateDict),
            "disabled": True,
            "updated_at": self.getCurrentTimeStr(),
        }
        documentRef.set(stateDict, merge=True)
        return self.normalizeProxyUsageStateDict(proxyStr, stateDict)

    def getFirestoreProxyDocumentRef(self, proxyStr: str):
        return (
            self.firestoreClient.collection(self.collectionNameStr)
            .document(self.getProxyIdStr(proxyStr))
        )

    def getRealtimeDatabaseProxyStateDict(self, proxyStr: str) -> dict:
        stateValue = self.getRealtimeDatabaseProxyRef(proxyStr).get()
        if isinstance(stateValue, dict):
            return stateValue

        return {}

    def recordRealtimeDatabaseProxyUsage(
        self,
        proxyStr: str,
        usageRecordDict: dict,
    ) -> dict:
        proxyRef = self.getRealtimeDatabaseProxyRef(proxyStr)
        currentStateDict = self.getRealtimeDatabaseProxyStateDict(proxyStr)
        usageCountInt = self.getUsageCountInt(currentStateDict) + 1
        disabledBool = bool(currentStateDict.get("disabled"))
        usedAtStr = str(usageRecordDict.get("used_at") or self.getCurrentTimeStr())
        stateDict = {
            "proxy": proxyStr,
            "usage_count": usageCountInt,
            "disabled": disabledBool,
            "updated_at": usedAtStr,
        }
        proxyRef.update(stateDict)
        self.pushRealtimeHistoryRecord(proxyRef, usageRecordDict)
        return self.normalizeProxyUsageStateDict(proxyStr, stateDict)

    def markRealtimeDatabaseProxyDisabled(self, proxyStr: str) -> dict:
        proxyRef = self.getRealtimeDatabaseProxyRef(proxyStr)
        currentStateDict = self.getRealtimeDatabaseProxyStateDict(proxyStr)
        stateDict = {
            "proxy": proxyStr,
            "usage_count": self.getUsageCountInt(currentStateDict),
            "disabled": True,
            "updated_at": self.getCurrentTimeStr(),
        }
        proxyRef.update(stateDict)
        return self.normalizeProxyUsageStateDict(proxyStr, stateDict)

    def pushRealtimeHistoryRecord(self, proxyRef, usageRecordDict: dict) -> None:
        pushedRef = proxyRef.child("history").push()
        if hasattr(pushedRef, "set"):
            pushedRef.set(usageRecordDict)
            return None

        return None

    def getRealtimeDatabaseProxyRef(self, proxyStr: str):
        return (
            self.realtimeDatabaseReference.child(self.usageHistoryPathStr)
            .child("proxy")
            .child(self.getProxyIdStr(proxyStr))
        )

    def getFallbackProxyStateDict(self, proxyStr: str) -> dict:
        proxyIdStr = self.getProxyIdStr(proxyStr)
        return self.fallbackUsageStateByProxyIdDict.get(
            proxyIdStr,
            {
                "proxy": proxyStr,
                "usage_count": 0,
                "disabled": False,
                "history": [],
            },
        )

    def recordFallbackProxyUsage(self, proxyStr: str, usageRecordDict: dict) -> dict:
        proxyIdStr = self.getProxyIdStr(proxyStr)
        currentStateDict = dict(self.getFallbackProxyStateDict(proxyStr))
        usageHistoryList = list(currentStateDict.get("history") or [])
        usageHistoryList.append(usageRecordDict)
        self.fallbackUsageHistoryList.append(usageRecordDict)
        stateDict = {
            "proxy": proxyStr,
            "usage_count": self.getUsageCountInt(currentStateDict) + 1,
            "disabled": bool(currentStateDict.get("disabled")),
            "updated_at": str(usageRecordDict.get("used_at") or self.getCurrentTimeStr()),
            "history": usageHistoryList,
        }
        self.fallbackUsageStateByProxyIdDict[proxyIdStr] = stateDict
        return self.normalizeProxyUsageStateDict(proxyStr, stateDict)

    def markFallbackProxyDisabled(self, proxyStr: str) -> dict:
        proxyIdStr = self.getProxyIdStr(proxyStr)
        currentStateDict = dict(self.getFallbackProxyStateDict(proxyStr))
        currentStateDict["proxy"] = proxyStr
        currentStateDict["usage_count"] = self.getUsageCountInt(currentStateDict)
        currentStateDict["disabled"] = True
        currentStateDict["updated_at"] = self.getCurrentTimeStr()
        self.fallbackUsageStateByProxyIdDict[proxyIdStr] = currentStateDict
        return self.normalizeProxyUsageStateDict(proxyStr, currentStateDict)

    def buildUsageRecordDict(
        self,
        proxyStr: str,
        usageRecordDict: dict | None = None,
    ) -> dict:
        recordDict = dict(usageRecordDict or {})
        recordDict["proxy"] = proxyStr
        recordDict.setdefault("used_at", self.getCurrentTimeStr())
        return recordDict

    def normalizeProxyUsageStateDict(self, proxyStr: str, stateDict: dict | None) -> dict:
        safeStateDict = stateDict if isinstance(stateDict, dict) else {}
        return {
            "proxy": str(safeStateDict.get("proxy") or proxyStr),
            "usage_count": self.getUsageCountInt(safeStateDict),
            "disabled": bool(safeStateDict.get("disabled")),
            "storage_enabled": self.storageEnabledBool,
            "database_type": self.databaseTypeStr,
            "storage_status": self.storageStatusStr,
        }

    def getUsageCountInt(self, stateDict: dict | None) -> int:
        if not isinstance(stateDict, dict):
            return 0

        try:
            return max(0, int(stateDict.get("usage_count") or 0))
        except (TypeError, ValueError):
            return 0

    def recordStorageError(self, error: Exception) -> None:
        self.storageEnabledBool = False
        self.storageStatusStr = "storage_operation_failed"
        self.storageErrorStr = error.__class__.__name__

    def isFirestoreEnabled(self) -> bool:
        return (
            self.storageEnabledBool
            and self.databaseTypeStr == FIREBASE_DATABASE_TYPE_FIRESTORE_STR
            and self.firestoreClient is not None
        )

    def isRealtimeDatabaseEnabled(self) -> bool:
        return (
            self.storageEnabledBool
            and self.databaseTypeStr == FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR
            and self.realtimeDatabaseReference is not None
        )

    def normalizeDatabaseTypeStr(self, databaseTypeStr: str) -> str:
        normalizedDatabaseTypeStr = str(databaseTypeStr or "").strip().lower()
        if normalizedDatabaseTypeStr in {
            FIREBASE_DATABASE_TYPE_FIRESTORE_STR,
            FIREBASE_DATABASE_TYPE_REALTIME_DATABASE_STR,
        }:
            return normalizedDatabaseTypeStr

        return ""

    def normalizePathStr(self, pathStr: str) -> str:
        return str(pathStr or "").strip().strip("/")

    def getProxyIdStr(self, proxyStr: str) -> str:
        return hashStringValue(str(proxyStr or ""))

    def getCurrentTimeStr(self) -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
