from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "refresh_tokens" (
    "id" UUID NOT NULL PRIMARY KEY,
    "token_hash" VARCHAR(255) NOT NULL UNIQUE,
    "exp" TIMESTAMPTZ NOT NULL,
    "iat" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "revoked" BOOL NOT NULL DEFAULT False,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_refresh_tok_exp_986555" ON "refresh_tokens" ("exp", "revoked");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "refresh_tokens";"""


MODELS_STATE = (
    "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"
)
