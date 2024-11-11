from os import getenv

from google.oauth2 import service_account
import googleapiclient.discovery
from googleapiclient.errors import HttpError

from dataclasses import dataclass
import logging

from typing import Union


@dataclass
class MemberInfo:
    first_name: str = ""
    last_name: str = ""
    discord_nickname: str = ""
    server_nickname: str = ""
    in_spreadsheet: bool = False


class GoogleSheetsClient:
    def __init__(self, clients_secrets_path: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            clients_secrets_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )

        self.logger = logging.getLogger(__name__)

        self.google_service = googleapiclient.discovery.build(
            "sheets", "v4", credentials=self.credentials
        )
        self.sheets = self.google_service.spreadsheets()
        self.logger.info("Succesfully logged into Gsheet API")

    async def get_spreadsheet(self) -> Union[None, ResourceWarning]:
        """Returns the spreadsheet

        Returns:
            Union[None, ResourceWarning]: The spreadsheet or None if an error occured
        """
        try:
            result = (
                self.sheets.values()
                .get(spreadsheetId=getenv("GOOGLE_SPREADSHEET_ID"), range="A1:F1000")
                .execute()
            )

            return result
        except HttpError as error:
            self.logger.error(error.content)
            return None

    async def get_member_by_name(self, first_name: str, last_name: str) -> MemberInfo:
        """Get the member's information using first name and last name.

        Args:
            first_name (str): First name for the query
            last_name (str): Last name for the query
        """

        self.logger.info(f"Looking up {first_name} {last_name}")

        ss = await self.get_spreadsheet()
        if ss is None:
            return None

        values = ss.get("values", [])
        member_info = MemberInfo(first_name=first_name, last_name=last_name)

        for row_index in range(len(values)):
            lowered_names = list(map(lambda s: s.lower(), values[row_index][:2]))
            if lowered_names == [last_name.lower(), first_name.lower()]:
                member_info.in_spreadsheet = True
                if len(values) >= 3:
                    member_info.server_nickname = values[row_index][2]
                if len(values) >= 4:
                    member_info.discord_nickname = values[row_index][3]

                return member_info

        return member_info

    async def get_member_by_discord_name(self, discord_name: str) -> MemberInfo:
        """Get the member's information using the discord name
        Args:
            discord_name (str): discord name of the user
        """

        self.logger.info(f"Looking up user {discord_name}")

        ss = await self.get_spreadsheet()
        if ss is None:
            return None

        values = ss.get("values", [])
        member_info = MemberInfo(discord_nickname=discord_name)

        for row_index in range(len(values)):
            if len(values[row_index]) < 4:
                continue

            if values[row_index][3].lower() == discord_name:
                member_info.in_spreadsheet = True
                member_info.last_name = values[row_index][0]
                member_info.first_name = values[row_index][1]
                member_info.server_nickname = values[row_index][2]
                return member_info

        return member_info

    async def add_member(self, member_info: MemberInfo) -> bool:
        """Add the member in the spreadsheet. If the member is already in the spreadsheet, update informations about the member.

        Args:
            member_info (MemberInfo): The member's information.
        """

        self.logger.info(f"Adding {member_info.first_name} {member_info.last_name}")

        values = (await self.get_spreadsheet()).get("values", [])

        body = {
            "values": [
                [
                    member_info.last_name,
                    member_info.first_name,
                    member_info.server_nickname,
                    member_info.discord_nickname,
                ]
            ]
        }

        for row_index in range(len(values)):
            lowered_names = list(map(lambda s: s.lower(), values[row_index][:2]))
            if lowered_names == [
                member_info.last_name.lower(),
                member_info.first_name.lower(),
            ]:
                member_sheet_row = row_index + 1
                break
        else:
            self.logger.info("Member is not in the spreadsheet")
            try:
                (
                    self.sheets.values()
                    .append(
                        spreadsheetId=getenv("GOOGLE_SPREADSHEET_ID"),
                        range="A1",
                        valueInputOption="USER_ENTERED",
                        body=body,
                    )
                    .execute()
                )
            except HttpError as error:
                self.logger.error(error.content)
                return None

            return True

        self.logger.info("Member is already in the spreadsheet")
        try:
            (
                self.sheets.values()
                .update(
                    spreadsheetId=getenv("GOOGLE_SPREADSHEET_ID"),
                    range=f"A{member_sheet_row}:F{member_sheet_row}",
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )
        except HttpError as error:
            self.logger.error(error.content)
            return None

        return True
