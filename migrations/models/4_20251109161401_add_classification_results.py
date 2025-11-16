from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "classification" (
    "id" UUID NOT NULL PRIMARY KEY,
    "model_name" VARCHAR(100) NOT NULL,
    "status" VARCHAR(9) NOT NULL DEFAULT 'pending',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "dataset_id" UUID REFERENCES "dataset" ("id") ON DELETE CASCADE,
    "image_id" UUID REFERENCES "image" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "classification"."status" IS 'PENDING: pending\nRUNNING: running\nCOMPLETED: completed\nFAILED: failed';
        CREATE TABLE IF NOT EXISTS "classificationresult" (
    "id" UUID NOT NULL PRIMARY KEY,
    "label" VARCHAR(100) NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "model_name" VARCHAR(100),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "classification_id" UUID REFERENCES "classification" ("id") ON DELETE CASCADE,
    "image_id" UUID NOT NULL REFERENCES "image" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "classificationresult";
        DROP TABLE IF EXISTS "classification";"""


MODELS_STATE = (
    "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"
)
