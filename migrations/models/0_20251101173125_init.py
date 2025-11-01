from tortoise import BaseDBAsyncClient


RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "role" VARCHAR(10) NOT NULL DEFAULT 'viewer',
    "status" VARCHAR(9) NOT NULL DEFAULT 'pending',
    "institution" VARCHAR(50),
    "department" VARCHAR(50),
    "phone" VARCHAR(20),
    "is_verified" BOOL NOT NULL DEFAULT False,
    "is_superuser" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_login" TIMESTAMPTZ,
    "password_reset_token" VARCHAR(255),
    "password_reset_expires" TIMESTAMPTZ,
    "email_verification_token" VARCHAR(255),
    "email_verified_at" TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
CREATE INDEX IF NOT EXISTS "idx_users_usernam_266d85" ON "users" ("username");
COMMENT ON COLUMN "users"."role" IS 'ADMIN: admin\nRESEARCHER: researcher\nANALYST: analyst\nVIEWER: viewer';
COMMENT ON COLUMN "users"."status" IS 'ACTIVE: active\nINACTIVE: inactive\nSUSPENDED: suspended\nPENDING: pending';
COMMENT ON TABLE "users" IS 'User model for authentication and authorization.';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmW1v4jgQx79KlFc9qVcVtu1u0ekkKLnbnAqsCnTvdllFJjZgNXGysdOWrfrdz+MkhI"
    "SEI6gty4k3Ff17ZmL/Jn6I50l3PUwcfjLkJNAb2pPOkEvkj4x+rOnI91MVBIHGjjIMpYVS"
    "0JiLANlCihPkcCIlTLgdUF9Qj4EpBNNUCG3iBRoKxYwwQW0EBhpiWEleQH8o5QSiYs+WYS"
    "mbbhsgZPR7SCzhTYm0hkF+/SZlyjB5JDz517+zJpQ4OMOAYgigdEvMfaUNh2b7D2UJnRtb"
    "tueELkut/bnsAFuYhyHFJ+ADbVPCSIAEwUuIWOg4McpEinosBRGEZNFVnAqYTFDoAGj9t0"
    "nIbDV69ST4c/a7voIenpKDGUu2xyBtlAlg8fQcjSods1J1eNTVx+bN0buLX9QoPS6mgWpU"
    "RPRn5YgEilwV1xQkcRF1VllezVBQzHLhkMMpu/o6IBNA21HTXfRoOYRNxUz+Wz8/X4Pxtn"
    "mjSEorhdKTcyaaSd24qR61AdIUIUwz9bsCxWWffQR5froBx/PTUozQlKXoI84fvABbM8Rn"
    "VVCuOL4Mz0RIgaZL5968mhMacGFVfTmzXvuJ8+VfUAdtgTLjdCAZkQw8pwSiwUJXgTRlhx"
    "CzyQrQxPftWOr3lDxER63coanZ7pjdhoawS9mI3Rh9A8Zs3DQ0uf8SFNjyUDNizW7z+p/+"
    "QNox5My5GLFb0/gMVkuBK+aktklOauU5qa3kROIWId82K6n3G+bFJwwDsoLEXA3MW0MSl+"
    "evezJiZjdRKEu0/rD/yei2jXZD4yGHWASPGEhm98+Gthy8YnIuN8jNZWlqLvOZofJRVIRq"
    "bBVWnpzbVnmJjxD/o6UHEx8FwpWfJlVYZr0OKKMDm4RQaS9cOOwlwPomAOvlAOsrACm37k"
    "lAZbyCj9mWJzc6xErmdtYzx3MsXV9r0S2+PniJb9hWr3cNvXY5/+4owRzkWA47LUNuawqx"
    "NKJCyWZ3sAqWhz4JwviGpBrZjOsBbRatHRAYtoUK1s+2bBHUJcVks545rjh2PUl+/KQHYz"
    "kG3GPOPF6P1jAfmB2jP2h2PmXAt5sDA1rqSp3n1KOL3OqxCKJ9NgcfNfhX+9LrGvl7noXd"
    "4IsOfUKh8CzmPVgIL90EJGoCJnuJ4eMtE5v1PCR2p4mNO5/7anW8KS04PK7Pa9bzBfL69j"
    "v4nqQxGfbaCbq45oJvS2EJ745U+h4o89/Pw9hrXJblCJFHn0L+Kk6b8iiHKbTjKaRKF/HJ"
    "OSpMVZ9G62IcplIR6a0OFYUBDhNoBxMISrCTu6XaIQhjZN89ILnIrbR4da/MdrXJrbt5BT"
    "E0VXkAmtDPuNrdlK+CPdML6uBxy/G6SjhKbf6rFF6e2BcuV5tMVKhW0+juafn1jt/lnRYF"
    "p/CUX+u1s/dnH95dnH2QJqonC+X9mvc/+bwsr07LBYBXvPdcctnPesurLMgwNSpAjM33E2"
    "DtdLPqyLryyMplnXyiKLw1/qvf65bceKQuOZBDJgf4FVNbHGsO5eLbz4l1DUUYdWbXSuAd"
    "dZp/57leXfda+e0IArQk451uL8//AvCcBFY="
)
