from django.db import models
from api.btc import DetailedBlock as ApiBlock, Transaction as ApiTransaction
import pendulum


class Block(models.Model):
    """
    Represents a Bitcoin block, containing only the fields useful for the simulation purpose.
    """
    hash = models.CharField(max_length=64, db_index=True)
    height = models.IntegerField(unique=True)
    time = models.DateTimeField(db_index=True)
    weight = models.IntegerField()

    @classmethod
    def save_from_api(cls, api_block: ApiBlock):
        """
        Create and save a block from the API data.

        :param api_block: the block from the API
        """
        db_block = Block()
        db_block.hash = api_block['hash']
        db_block.time = pendulum.from_timestamp(api_block['time']).naive()
        db_block.weight = api_block['weight']
        db_block.height = api_block['height']
        db_block.save()
        # ignoring the coinbase transaction at index 0
        db_txs = [Transaction.to_unsaved_db_tx(api_tx, db_block) for api_tx in api_block['tx'][1:]]
        Transaction.objects.bulk_create(db_txs)

    def __str__(self):
        return f'<{Block.__name__} ' \
               f'hash="{self.hash[-8:]}" ' \
               f'height={self.height} ' \
               f'time={str(self.time)} ' \
               f'weight={self.weight}>'


class Transaction(models.Model):
    """
    Represents a Bitcoin transaction, containing only the fields useful for the simulation purpose.
    """
    hash = models.CharField(max_length=64, db_index=True)
    weight = models.IntegerField()
    fee = models.IntegerField()
    block = models.ForeignKey(Block, related_name='transactions', on_delete=models.CASCADE)

    @classmethod
    def to_unsaved_db_tx(cls, api_tx: ApiTransaction, block: Block):
        """
        Create a Transaction from API data, without saving it in the database.

        :param api_tx: The data from the API
        :param block: The block that contains the transaction
        :return: the transaction
        """
        db_tx = Transaction()
        db_tx.hash = api_tx['hash']
        db_tx.weight = api_tx['weight']
        db_tx.fee = api_tx['fee']
        db_tx.block = block
        return db_tx

    def __str__(self):
        return f'<{Transaction.__name__} ' \
               f'hash="{self.hash[-8:]}" ' \
               f'weight={str(self.weight)} ' \
               f'block="{self.block.hash[-8:]}">'
