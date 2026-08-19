import json
import os

import pyotp
from dotenv import load_dotenv
from neo_api_client import NeoAPI



def login():
    load_dotenv()

    client = NeoAPI(
        environment="prod",
        access_token=None,
        neo_fin_key=None,
        consumer_key=os.getenv("KOTAK_CONSUMER_KEY")
    )

    totp = pyotp.TOTP(
        os.getenv("KOTAK_TOTP_SECRET")
    ).now()

    login_response = client.totp_login(
        mobile_number=os.getenv("KOTAK_MOBILE_NUMBER"),
        ucc=os.getenv("KOTAK_UCC"),
        totp=totp
    )

    print("TOTP login completed.")

    validation_response = client.totp_validate(
        mpin=os.getenv("KOTAK_MPIN")
    )

    session_data = validation_response["data"]

    with open("token.json", "w") as file:
        json.dump(session_data, file, indent=4)

    print("Session information saved to token.json")


if __name__ == "__main__":
    login()





    