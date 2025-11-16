from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "dataset" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "owner_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "image" (
    "id" UUID NOT NULL PRIMARY KEY,
    "filename" VARCHAR(255) NOT NULL,
    "filepath" VARCHAR(512) NOT NULL,
    "uploaded_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "analyzed" BOOL NOT NULL DEFAULT False,
    "dataset_id" UUID NOT NULL REFERENCES "dataset" ("id") ON DELETE CASCADE,
    "device_id" UUID REFERENCES "device" ("id") ON DELETE CASCADE,
    "uploaded_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "image";
        DROP TABLE IF EXISTS "dataset";"""


MODELS_STATE = (
    "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"
    "HuD2Pdh38="
)
