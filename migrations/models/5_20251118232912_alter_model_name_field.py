from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "classification" ALTER COLUMN "model_name" DROP NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "classification" ALTER COLUMN "model_name" SET NOT NULL;"""


MODELS_STATE = (
    "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"
    "0Pz9P74/G0E="
)
