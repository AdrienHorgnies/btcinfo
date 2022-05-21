"""
API calls to https://blockchain.info, and relevant models
"""

import logging
from typing import TypedDict, List

import requests

BASE_URL = 'https://blockchain.info'

log = logging.getLogger(__name__)


class BlockchainExplorerError(Exception):
    def __init__(self, resource, response_body):
        """
        An error representing a failed request to Blockchain Data API

        :param response_body: The response body of the failed request
        """
        self.resource = resource
        self.status_code = response_body['status_code']
        self.message = response_body['message']

    def __str__(self):
        return f'<{BlockchainExplorerError.__name__} ' \
               f'resource={self.resource} ' \
               f'code={self.status_code} ' \
               f'message="{self.message}">'


class Transaction(TypedDict):
    hash: str
    ver: int
    vin_sz: int
    vout_sz: int
    size: int
    weight: int
    fee: int
    relayed_by: str  # IP of node that sent the transaction
    lock_time: int  # UNIX timestamp or block height, unused.
    tx_index: int
    double_spend: bool
    time: str
    block_index: int
    block_height: int
    inputs: List
    out: List


class BriefBlock(TypedDict):
    hash: str  # 64 char
    height: int  # offset compared to genesis block
    time: int  # UNIX timestamp, start of mining
    block_index: int  # same as block height ?


class DetailedBlock(TypedDict):
    hash: str  # 64 char, hash of the block
    ver: int  # version
    prev_block: str  # 64 char, hash of the previous block
    mrkl_block: str  # 64 char, hash of the Merkle tree
    time: int  # UNIX timestamp
    bits: int  # ???
    next_block: List[str]  # List of hashes of the next blocks
    fee: int  # total fees collected by miner
    nonce: int  # arbitrary number to make the current block hash match the difficulty
    n_tx: int  # number of transactions
    size: int  # ??? Size in bytes ?
    block_index: int  # same as block height ?
    main_chain: bool  # If it's in the longest blockchain
    height: int  # offset compared to genesis block ?
    weight: int  # weight of the block
    tx: List  # Let's see... fingers crossed


def get_blocks(datetime) -> List[BriefBlock]:
    """

    :param datetime: 0AM of the day you want the blocks for
    :return: The list of blocks for the day starting at datetime, ordered from newest to oldest
    """
    log.info(f"Getting blocks for {datetime.to_formatted_date_string()}")
    timestamp_ms = round(datetime.timestamp() * 1000)

    url = BASE_URL + f'/blocks/{timestamp_ms}?format=json'
    response = requests.get(url)

    response_body = response.json()
    if response.status_code != 200:
        log.error(f'Failed to get blocks for {datetime.to_formatted_date_string()} : {response_body["message"]}')
        raise BlockchainExplorerError(response, response_body)

    log.info(f"Received blocks for {datetime.to_formatted_date_string()}")
    return response_body


def get_block(block_hash) -> DetailedBlock:
    """

    :param block_hash: hash of the block to get the details of
    :return: the block with its details
    """
    url = BASE_URL + f'/rawblock/{block_hash}'
    response = requests.get(url)

    response_body = response.json()
    if response.status_code != 200:
        log.error(f'Failed to get block {block_hash} : {response_body["message"]}')
        raise BlockchainExplorerError(response_body, response_body)

    return response_body
