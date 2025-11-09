from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "device" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "hostname" VARCHAR(255) NOT NULL UNIQUE,
    "location" VARCHAR(255),
    "firmware_version" VARCHAR(50),
    "is_online" BOOL NOT NULL DEFAULT False,
    "last_seen" TIMESTAMPTZ,
    "registered_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "device";"""


MODELS_STATE = (
    "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"
)
