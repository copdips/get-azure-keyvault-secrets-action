import argparse
import asyncio
import http.client
import json
import os

KEYVAULT_API_VERSION = "7.4"
FORBIDDEN_ENV_VAR_PREFIX = "GITHUB_"
GITHUB_OUTPUT_JSON_VAR_NAME = "json"


async def fetch(keyvault, secret, access_token):
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, make_request, keyvault, secret, access_token)
    return await future


def make_request(keyvault, secret, access_token):
    conn = http.client.HTTPSConnection(f"{keyvault}.vault.azure.net")
    conn.request(
        "GET",
        f"/secrets/{secret}?api-version={KEYVAULT_API_VERSION}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    res = conn.getresponse()
    data = res.read()
    value = json.loads(data)["value"]
    return {"secret": secret, "value": value}


def format_to_env_vars(result_list: list) -> dict:
    return {
        result["secret"].upper().replace("-", "_"): result["value"]
        for result in result_list
    }


def write_results_to_env_vars(result_dict: dict):
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
        for k, v in result_dict.items():
            if k.startswith(FORBIDDEN_ENV_VAR_PREFIX):
                msg = f"env var {k} has forbidden prefix {FORBIDDEN_ENV_VAR_PREFIX}."
                print(f"::error:: {msg}")
                raise ValueError(msg)
            f.write(f"{k}={v}\n")
            print(f"::add-mask::{v}")
            print(f"Created new env var: {k}")
    print(f"GITHUB_OUTPUT: {os.environ['GITHUB_OUTPUT']}")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
        f.write(f"{GITHUB_OUTPUT_JSON_VAR_NAME}={json.dumps(result_dict)}\n")
    with open(os.environ["GITHUB_OUTPUT"], encoding="utf-8") as f:
        print(f.read())


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyvault", help="azure keyvault name", required=True)
    parser.add_argument(
        "--secrets",
        help="comma separated list of secret names",
        required=True,
    )
    parser.add_argument(
        "--access-token",
        help="azure keyvault access token",
        required=True,
    )
    args = parser.parse_args()
    keyvault = args.keyvault
    secrets = args.secrets.split(",")
    print(f"keyvault: {args.keyvault}")
    print(f"secrets: {args.secrets}")
    access_token = args.access_token
    tasks = [fetch(keyvault, secret, access_token) for secret in secrets]

    results_raw = await asyncio.gather(*tasks)
    results_for_env_vars = format_to_env_vars(results_raw)
    write_results_to_env_vars(results_for_env_vars)


if __name__ == "__main__":
    asyncio.run(main())
