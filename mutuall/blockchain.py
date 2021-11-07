import hashlib
import json
from uuid import uuid4
import jsonpickle
from flask import Flask
from urllib.parse import urlparse
from Crypto.PublicKey import RSA
from Crypto.Signature import *
from time import time
from datetime import datetime
import requests


class Blockchain (object):
	def __init__(self):
		self.chain = [self.addGenesisBlock()];
		self.pendingTransactions = [];
		self.difficulty = 2;
		self.minerRewards = 50;
		self.donation = 0;
		self.blockSize = 10;
		self.nodes = set();
		self.mutualTransactions = [];
		self.mutualChain = [self.addGenesisBlock(isMutual=True)];

	def register_node(self, address):
		parsedUrl = urlparse(address)
		self.nodes.add(parsedUrl.netloc)

	def resolveConflicts(self, isMutual=False):
		neighbors = self.nodes;
		newChain = None;

		if isMutual:
			maxLength = len(self.mutualChain);

			for node in neighbors:
				response = requests.get(f'http://{node}/mutualChain');

				if response.status_code == 200:
					length = response.json()['length'];
					mutualChain = response.json()['mutualChain'];

					if length > maxLength and self.isValidChain():
						maxLength = length;
						newChain = mutualChain;

				if newChain:
					self.mutualChain = self.chainJSONdecode(newChain);
					print(self.mutualChain);
					return True;

			return False;

		maxLength = len(self.chain);

		for node in neighbors:
			response = requests.get(f'http://{node}/chain');

			if response.status_code == 200:
				length = response.json()['length'];
				chain = response.json()['chain'];

				if length > maxLength and self.isValidChain():
					maxLength = length;
					newChain = chain;

		if newChain:
			self.chain = self.chainJSONdecode(newChain);
			print(self.chain);
			return True;

		return False;

	def minePendingTransactions(self, miner):
		
		lenPT = len(self.pendingTransactions);
		if(lenPT <= 1):
			print("Not enough transactions to mine! (Must be > 1)")
			return False;
		else:
			for i in range(0, lenPT, self.blockSize):

				end = i + self.blockSize;
				if i >= lenPT:
					end = lenPT;
				
				transactionSlice = self.pendingTransactions[i:end];

				newBlock = Block(transactionSlice, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), len(self.chain));
				#print(type(self.getLastBlock()));

				hashVal = self.getLastBlock().hash;
				newBlock.prev = hashVal;
				newBlock.mineBlock(self.difficulty);
				self.chain.append(newBlock);
			print("Mining Transactions Success!");

			payMiner = Transaction("Miner Rewards", miner, self.minerRewards);
			self.pendingTransactions = [payMiner];
		return True;

	def mineMutualTransactions(self):
		lenMT = len(self.mutualTransactions);
		if(lenMT < 1):
			print("Not enough transactions to mine! (Must be > 1)")
			return False;
		else:
			for i in range(0, lenMT, self.blockSize):

				end = i + self.blockSize;
				if i >= lenMT:
					end = lenMT;
				
				transactionSlice = self.mutualTransactions[i:end];

				newBlock = MutualBlock(transactionSlice, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), len(self.chain));
				#print(type(self.getLastBlock()));

				hashVal = self.getLastBlock(isMutual=True).hash;
				newBlock.prev = hashVal;
				newBlock.mineBlock(self.difficulty);
				self.mutualChain.append(newBlock);
			print("Mining Transactions Success!");

			payParticipants = MutualAidTransaction(self.donation);
			self.mutualTransactions = [payParticipants];
			self.donations = 0
		return True;

	def addTransaction(self, sender, reciever, amt, keyString, senderKey):
		keyByte = keyString.encode("ASCII");
		senderKeyByte = senderKey.encode("ASCII");

		#print(type(keyByte), keyByte);

		key = RSA.import_key(keyByte);
		senderKey = RSA.import_key(senderKeyByte);

		if not sender or not reciever or not amt:
			print("transaction error 1");
			return False;

		transaction = Transaction(sender, reciever, 0.98*amt);

		transaction.signTransaction(key, senderKey);

		if not transaction.isValidTransaction():
			print("transaction error 2");
			return False;
		self.pendingTransactions.append(transaction);
		return len(self.chain) + 1;

	def addMutualAidTransaction(self, amt, keyString, patronKey):
		keyByte = keyString.encode("ASCII");
		patronKeyByte = patronKey.encode("ASCII");

		key = RSA.import_key(keyByte);
		patronKey = RSA.import_key(patronKeyByte);

		if not amt:
			print("mutual aid transaction error")
			return False;

		transaction = MutualAidTransaction(amt)
		transaction.signTransaction(key, patronKey)

		if not transaction.isValidTransaction():
			print("mutual aid transaction error 2")
			return False;

		# Todo create an array for mutualTransactions
		self.donation += amt;
		self.mutualTransactions.append(transaction)
		return len(self.mutualChain) + 1




	def getLastBlock(self, isMutual=False):
		if isMutual:
			self.mutualChain[-1];
		return self.chain[-1];

	def addGenesisBlock(self, isMutual=False):
		tArr = [];
		if isMutual:
			tArr.append(MutualAidTransaction(2));
			genesis = MutualBlock(tArr, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 0);
		tArr.append(Transaction("me", "you", 10));
		genesis = Block(tArr, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 0);

		genesis.prev = "None";
		return genesis;


	def isValidChain(self, isMutual=False):
		if isMutual:
			for i in range(1, len(self.mutualChain)):
				b1 = self.mutualChain[i-1];
				b2 = self.mutualChain[i];

				if not b2.hasValidTransactions():
					print("error 3");
					return False;

				if b2.hash != b2.calculateHash():
					print("error 4");
					return False;


				if b2.prev != b1.hash:
					console.log("error 5");
					return False;
		for i in range(1, len(self.chain)):
			b1 = self.chain[i-1];
			b2 = self.chain[i];

			if not b2.hasValidTransactions():
				print("error 3");
				return False;

			if b2.hash != b2.calculateHash():
				print("error 4");
				return False;


			if b2.prev != b1.hash:
				console.log("error 5");
				return False;
		return True;

	def generateKeys(self):
		key = RSA.generate(2048)
		private_key = key.export_key()
		file_out = open("private.pem", "wb")
		file_out.write(private_key)

		public_key = key.publickey().export_key()
		file_out = open("receiver.pem", "wb")
		file_out.write(public_key)
		
		print(public_key.decode('ASCII'));
		return key.publickey().export_key().decode('ASCII');


	def chainJSONencode(self, isMutual=False):

		blockArrJSON = [];

		if isMutual:
			for block in self.mutualChain:
				blockJSON = {};
				blockJSON['hash'] = block.hash;
				blockJSON['index'] = block.index;
				blockJSON['prev'] = block.prev;
				blockJSON['time'] = block.time;
				blockJSON['nonse'] = block.nonse;
				blockJSON['mutual'] = block.mutual;


				transactionsJSON = [];
				tJSON = {};
				for transaction in block.transactions:
					tJSON['amount'] = transaction.amount;
					tJSON['hash'] = transaction.hash;
					transactionsJSON.append(tJSON);

				blockJSON['transactions'] = transactionsJSON;

				blockArrJSON.append(blockJSON);

		for block in self.chain:
			blockJSON = {};
			blockJSON['hash'] = block.hash;
			blockJSON['index'] = block.index;
			blockJSON['prev'] = block.prev;
			blockJSON['time'] = block.time;
			blockJSON['nonse'] = block.nonse;
			blockJSON['gym'] = block.gym;


			transactionsJSON = [];
			tJSON = {};
			for transaction in block.transactions:
				tJSON['time'] = transaction.time;
				tJSON['sender'] = transaction.sender;
				tJSON['reciever'] = transaction.reciever;
				tJSON['amt'] = transaction.amt;
				tJSON['hash'] = transaction.hash;
				transactionsJSON.append(tJSON);

			blockJSON['transactions'] = transactionsJSON;

			blockArrJSON.append(blockJSON);

		return blockArrJSON;

	def chainJSONdecode(self, chainJSON, isMutual=False):
		chain=[];
		for blockJSON in chainJSON:
			tArr = [];
			for tJSON in blockJSON['transactions']:
				if isMutual:
					transaction = MutualAidTransaction(tJSON['amt']);
					transaction.hash = tJSON['hash'];
				else:
					transaction = Transaction(tJSON['sender'], tJSON['reciever'], tJSON['amt']);
					transaction.time = tJSON['time'];
					transaction.hash = tJSON['hash'];
				tArr.append(transaction);

			if  isMutual:
				block = MutualBlock(tArr, blockJSON['time'], blockJSON['index']);
				block.hash = blockJSON['hash'];
				block.prev = blockJSON['prev'];
				block.nonse = blockJSON['nonse'];
				block.mutual = blockJSON['mutual'];
			else:
				block = Block(tArr, blockJSON['time'], blockJSON['index']);
				block.hash = blockJSON['hash'];
				block.prev =blockJSON['prev'];
				block.nonse = blockJSON['nonse'];
				block.gym = blockJSON['gym'];


			chain.append(block);
		return chain;
		
	def getBalance(self, person=None, isMutual=False):
		balance = 0; 
		if isMutual:
			return self.donation;
		for i in range(1, len(self.chain)):
			block = self.chain[i];
			try:
				for j in range(0, len(block.transactions)):
					transaction = block.transactions[j];
					if(transaction.sender == person):
						balance -= transaction.amt;
					if(transaction.reciever == person):
						balance += transaction.amt;
			except AttributeError:
				print("no transaction")
		return balance + 100;


class MutualBlock(object):
	def calculateMutual(self):
		return '30d';

	def calculateHash(self):
		hashTransactions = "";

		for transaction in self.transactions:
			hashTransactions += transaction.hash;
		hashString = str(self.time) + hashTransactions + self.mutual + self.prev + str(self.nonse);
		hashEncoded = json.dumps(hashString, sort_keys=True).encode();
		return hashlib.sha256(hashEncoded).hexdigest();

	def __init__(self, transactions, time, index):
		self.index = index;
		self.transactions = transactions
		self.time = time;
		self.prev = ''
		self.nonse = 0;
		self.mutual = self.calculateMutual()
		self.hash = self.calculateHash();

		def calculateMutual(self):
			return '30d';

		

		# TODO:  Make this block automines itself after 30days 

	def mineBlock(self, difficulty):
		arr = [];
		for i in range(0, difficulty):
			arr.append(i);
		
		#compute until the beginning of the hash = 0123..difficulty
		arrStr = map(str, arr);  
		hashPuzzle = ''.join(arrStr);
		#print(len(hashPuzzle));
		while self.hash[0:difficulty] != hashPuzzle:
			self.nonse += 1;
			self.hash = self.calculateHash();
			#print(len(hashPuzzle));
			#print(self.hash[0:difficulty]);
		print("Block Mined!");
		return True;

	def hasValidTransactions(self):
		for i in range(0, len(self.transactions)):
			transaction = self.transactions[i];
			if not transaction.isValidTransaction():
				return False;
			return True;
	
	def JSONencode(self):
		return jsonpickle.encode(self);



class Block (object):
	def __init__(self, transactions, time, index):
		self.index = index;
		self.transactions = transactions;
		self.time = time;
		self.prev = '';
		self.nonse = 0;
		self.gym = self.calculateGym();
		self.hash = self.calculateHash();

	def calculateGym(self):
		return "24 hr";

	def calculateHash(self):

		hashTransactions = "";

		for transaction in self.transactions:
			hashTransactions += transaction.hash;
		hashString = str(self.time) + hashTransactions + self.gym + self.prev + str(self.nonse);
		hashEncoded = json.dumps(hashString, sort_keys=True).encode();
		return hashlib.sha256(hashEncoded).hexdigest();

	def mineBlock(self, difficulty):
		arr = [];
		for i in range(0, difficulty):
			arr.append(i);
		
		#compute until the beginning of the hash = 0123..difficulty
		arrStr = map(str, arr);  
		hashPuzzle = ''.join(arrStr);
		#print(len(hashPuzzle));
		while self.hash[0:difficulty] != hashPuzzle:
			self.nonse += 1;
			self.hash = self.calculateHash();
			#print(len(hashPuzzle));
			#print(self.hash[0:difficulty]);
		print("Block Mined!");
		return True;

	def hasValidTransactions(self):
		for i in range(0, len(self.transactions)):
			transaction = self.transactions[i];
			if not transaction.isValidTransaction():
				return False;
			return True;
	
	def JSONencode(self):
		return jsonpickle.encode(self);


class MutualAidTransaction(object):
	def __init__(self, amount):
		self.sender = "Someone"
		self.reciever = "Participant"
		self.time = "today"
		self.amount = amount;
		self.hash = self.calculateHash();

	def calculateHash(self):
		hashString = self.sender + self.reciever + str(self.amount) + str(self.time);
		hashEncoded = json.dumps(hashString, sort_keys=True).encode();
		return hashlib.sha256(hashEncoded).hexdigest();

	def isValidTransaction(self):
		if(self.hash != self.calculateHash()):
			return False;
		return True;

	def signTransaction(self, key, senderKey):
		if(self.hash != self.calculateHash()):
			print("transaction tampered error");
			return False;

		pkcs1_15.new(key);

		self.signature = "made";
		print("made signature!");
		return True;


	
class Transaction (object):
	def __init__(self, sender, reciever, amt):
		self.sender = sender;
		self.reciever = reciever;
		self.amt = amt;
		self.time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"); #change to current date
		self.hash = self.calculateHash();


	def calculateHash(self):
		hashString = self.sender + self.reciever + str(self.amt) + str(self.time);
		hashEncoded = json.dumps(hashString, sort_keys=True).encode();
		return hashlib.sha256(hashEncoded).hexdigest();

	def isValidTransaction(self):

		if(self.hash != self.calculateHash()):
			return False;
		if(self.sender == self.reciever):
			return False;
		if(self.sender == "Miner Rewards"):
			#security : unfinished
			return True;
		if not self.signature or len(self.signature) == 0:
			print("No Signature!")
			return False;
		return True;
		#needs work!

	def signTransaction(self, key, senderKey):
		if(self.hash != self.calculateHash()):
			print("transaction tampered error");
			return False;
		#print(str(key.publickey().export_key()));
		#print(self.sender);
		if(str(key.publickey().export_key()) != str(senderKey.publickey().export_key())):
			print("Transaction attempt to be signed from another wallet");
			return False;

		#h = MD5.new(self.hash).digest();

		pkcs1_15.new(key);

		self.signature = "made";
		#print(key.sign(self.hash, ""));
		print("made signature!");
		return True;