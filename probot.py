import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from dotenv import load_dotenv
import asyncio
from web3 import Web3, WebsocketProvider
from datetime import datetime
import requests
import psycopg2
import json

load_dotenv()

DATABASE_TOKEN = os.getenv('DATABASE_TOKEN')
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')
RESERVOIR_API_KEY = os.getenv('RESERVOIR_API_KEY')
prohibitionContract = "0x47A91457a3a1f700097199Fd63c039c4784384aB"

# Set up web3
#w3 = Web3(WebsocketProvider('wss://arb-mainnet.g.alchemy.com/v2/' + ALCHEMY_API_KEY))

# Contract address and ABI
contract_address = '0x47A91457a3a1f700097199Fd63c039c4784384aB'
contract_abi = '[{"inputs":[{"internalType":"string","name":"_tokenName","type":"string"},{"internalType":"string","name":"_tokenSymbol","type":"string"},{"internalType":"address","name":"_renderProviderAddress","type":"address"},{"internalType":"address","name":"_platformProviderAddress","type":"address"},{"internalType":"address","name":"_randomizerContract","type":"address"},{"internalType":"address","name":"_adminACLContract","type":"address"},{"internalType":"uint248","name":"_startingProjectId","type":"uint248"},{"internalType":"bool","name":"_autoApproveArtistSplitProposals","type":"bool"},{"internalType":"address","name":"_engineRegistryContract","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"AcceptedArtistAddressesAndSplits","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"approved","type":"address"},{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"bool","name":"approved","type":"bool"}],"name":"ApprovalForAll","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"_projectId","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"_index","type":"uint256"}],"name":"ExternalAssetDependencyRemoved","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"_projectId","type":"uint256"},{"indexed":true,"internalType":"uint256","name":"_index","type":"uint256"},{"indexed":false,"internalType":"string","name":"_cid","type":"string"},{"indexed":false,"internalType":"enum IGenArt721CoreContractV3_Engine_Flex.ExternalAssetDependencyType","name":"_dependencyType","type":"uint8"},{"indexed":false,"internalType":"uint24","name":"_externalAssetDependencyCount","type":"uint24"}],"name":"ExternalAssetDependencyUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"enum IGenArt721CoreContractV3_Engine_Flex.ExternalAssetDependencyType","name":"_dependencyType","type":"uint8"},{"indexed":false,"internalType":"string","name":"_gatewayAddress","type":"string"}],"name":"GatewayUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_to","type":"address"},{"indexed":true,"internalType":"uint256","name":"_tokenId","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"_currentMinter","type":"address"}],"name":"MinterUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"_field","type":"bytes32"}],"name":"PlatformUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"ProjectExternalAssetDependenciesLocked","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"_projectId","type":"uint256"},{"indexed":true,"internalType":"bytes32","name":"_update","type":"bytes32"}],"name":"ProjectUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"_projectId","type":"uint256"},{"indexed":false,"internalType":"address","name":"_artistAddress","type":"address"},{"indexed":false,"internalType":"address","name":"_additionalPayeePrimarySales","type":"address"},{"indexed":false,"internalType":"uint256","name":"_additionalPayeePrimarySalesPercentage","type":"uint256"},{"indexed":false,"internalType":"address","name":"_additionalPayeeSecondarySales","type":"address"},{"indexed":false,"internalType":"uint256","name":"_additionalPayeeSecondarySalesPercentage","type":"uint256"}],"name":"ProposedArtistAddressesAndSplits","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"string","name":"_projectName","type":"string"},{"internalType":"address payable","name":"_artistAddress","type":"address"}],"name":"addProject","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_cidOrData","type":"string"},{"internalType":"enum IGenArt721CoreContractV3_Engine_Flex.ExternalAssetDependencyType","name":"_dependencyType","type":"uint8"}],"name":"addProjectExternalAssetDependency","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_script","type":"string"}],"name":"addProjectScript","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_sender","type":"address"},{"internalType":"address","name":"_contract","type":"address"},{"internalType":"bytes4","name":"_selector","type":"bytes4"}],"name":"adminACLAllowed","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_sender","type":"address"},{"internalType":"address","name":"_contract","type":"address"},{"internalType":"bytes4","name":"_selector","type":"bytes4"},{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"adminACLAllowed","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"adminACLContract","outputs":[{"internalType":"contract IAdminACLV0","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"address payable","name":"_artistAddress","type":"address"},{"internalType":"address payable","name":"_additionalPayeePrimarySales","type":"address"},{"internalType":"uint256","name":"_additionalPayeePrimarySalesPercentage","type":"uint256"},{"internalType":"address payable","name":"_additionalPayeeSecondarySales","type":"address"},{"internalType":"uint256","name":"_additionalPayeeSecondarySalesPercentage","type":"uint256"}],"name":"adminAcceptArtistAddressesAndSplits","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"artblocksDependencyRegistryAddress","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"autoApproveArtistSplitProposals","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"coreType","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[],"name":"coreVersion","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[],"name":"defaultBaseURI","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"forbidNewProjects","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getApproved","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_index","type":"uint256"}],"name":"getHistoricalRandomizerAt","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_price","type":"uint256"}],"name":"getPrimaryRevenueSplits","outputs":[{"internalType":"uint256","name":"renderProviderRevenue_","type":"uint256"},{"internalType":"address payable","name":"renderProviderAddress_","type":"address"},{"internalType":"uint256","name":"platformProviderRevenue_","type":"uint256"},{"internalType":"address payable","name":"platformProviderAddress_","type":"address"},{"internalType":"uint256","name":"artistRevenue_","type":"uint256"},{"internalType":"address payable","name":"artistAddress_","type":"address"},{"internalType":"uint256","name":"additionalPayeePrimaryRevenue_","type":"uint256"},{"internalType":"address payable","name":"additionalPayeePrimaryAddress_","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenId","type":"uint256"}],"name":"getRoyalties","outputs":[{"internalType":"address payable[]","name":"recipients","type":"address[]"},{"internalType":"uint256[]","name":"bps","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"operator","type":"address"}],"name":"isApprovedForAll","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_minter","type":"address"}],"name":"isMintWhitelisted","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"lockProjectExternalAssetDependencies","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_to","type":"address"},{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"address","name":"_by","type":"address"}],"name":"mint_Ecf","outputs":[{"internalType":"uint256","name":"_tokenId","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"minterContract","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"newProjectsForbidden","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"nextProjectId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"numHistoricalRandomizers","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"ownerOf","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"platformProviderPrimarySalesAddress","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"platformProviderPrimarySalesPercentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"platformProviderSecondarySalesAddress","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"platformProviderSecondarySalesBPS","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"preferredArweaveGateway","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"preferredIPFSGateway","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectArtistPaymentInfo","outputs":[{"internalType":"address","name":"artistAddress","type":"address"},{"internalType":"address","name":"additionalPayeePrimarySales","type":"address"},{"internalType":"uint256","name":"additionalPayeePrimarySalesPercentage","type":"uint256"},{"internalType":"address","name":"additionalPayeeSecondarySales","type":"address"},{"internalType":"uint256","name":"additionalPayeeSecondarySalesPercentage","type":"uint256"},{"internalType":"uint256","name":"secondaryMarketRoyaltyPercentage","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectDetails","outputs":[{"internalType":"string","name":"projectName","type":"string"},{"internalType":"string","name":"artist","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"string","name":"website","type":"string"},{"internalType":"string","name":"license","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_index","type":"uint256"}],"name":"projectExternalAssetDependencyByIndex","outputs":[{"components":[{"internalType":"string","name":"cid","type":"string"},{"internalType":"enum IGenArt721CoreContractV3_Engine_Flex.ExternalAssetDependencyType","name":"dependencyType","type":"uint8"},{"internalType":"address","name":"bytecodeAddress","type":"address"},{"internalType":"string","name":"data","type":"string"}],"internalType":"struct IGenArt721CoreContractV3_Engine_Flex.ExternalAssetDependencyWithData","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectExternalAssetDependencyCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectIdToAdditionalPayeePrimarySales","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectIdToAdditionalPayeePrimarySalesPercentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectIdToAdditionalPayeeSecondarySales","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectIdToAdditionalPayeeSecondarySalesPercentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectIdToArtistAddress","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectIdToSecondaryMarketRoyaltyPercentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_index","type":"uint256"}],"name":"projectScriptByIndex","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_index","type":"uint256"}],"name":"projectScriptBytecodeAddressByIndex","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectScriptDetails","outputs":[{"internalType":"string","name":"scriptTypeAndVersion","type":"string"},{"internalType":"string","name":"aspectRatio","type":"string"},{"internalType":"uint256","name":"scriptCount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectStateData","outputs":[{"internalType":"uint256","name":"invocations","type":"uint256"},{"internalType":"uint256","name":"maxInvocations","type":"uint256"},{"internalType":"bool","name":"active","type":"bool"},{"internalType":"bool","name":"paused","type":"bool"},{"internalType":"uint256","name":"completedTimestamp","type":"uint256"},{"internalType":"bool","name":"locked","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"projectURIInfo","outputs":[{"internalType":"string","name":"projectBaseURI","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"address payable","name":"_artistAddress","type":"address"},{"internalType":"address payable","name":"_additionalPayeePrimarySales","type":"address"},{"internalType":"uint256","name":"_additionalPayeePrimarySalesPercentage","type":"uint256"},{"internalType":"address payable","name":"_additionalPayeeSecondarySales","type":"address"},{"internalType":"uint256","name":"_additionalPayeeSecondarySalesPercentage","type":"uint256"}],"name":"proposeArtistPaymentAddressesAndSplits","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"proposedArtistAddressesAndSplitsHash","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"randomizerContract","outputs":[{"internalType":"contract IRandomizerV2","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_index","type":"uint256"}],"name":"removeProjectExternalAssetDependency","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"removeProjectLastScript","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"renderProviderPrimarySalesAddress","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renderProviderPrimarySalesPercentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renderProviderSecondarySalesAddress","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renderProviderSecondarySalesBPS","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"operator","type":"address"},{"internalType":"bool","name":"approved","type":"bool"}],"name":"setApprovalForAll","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenId","type":"uint256"},{"internalType":"bytes32","name":"_hashSeed","type":"bytes32"}],"name":"setTokenHash_8PT","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"startingProjectId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"toggleProjectIsActive","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"name":"toggleProjectIsPaused","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenId","type":"uint256"}],"name":"tokenIdToHash","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenId","type":"uint256"}],"name":"tokenIdToHashSeed","outputs":[{"internalType":"bytes12","name":"","type":"bytes12"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenId","type":"uint256"}],"name":"tokenIdToProjectId","outputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenId","type":"uint256"}],"name":"tokenURI","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_artblocksDependencyRegistryAddress","type":"address"}],"name":"updateArtblocksDependencyRegistryAddress","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"_gateway","type":"string"}],"name":"updateArweaveGateway","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"_defaultBaseURI","type":"string"}],"name":"updateDefaultBaseURI","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"_gateway","type":"string"}],"name":"updateIPFSGateway","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_address","type":"address"}],"name":"updateMinterContract","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"address payable","name":"_artistAddress","type":"address"}],"name":"updateProjectArtistAddress","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_projectArtistName","type":"string"}],"name":"updateProjectArtistName","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_aspectRatio","type":"string"}],"name":"updateProjectAspectRatio","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_newBaseURI","type":"string"}],"name":"updateProjectBaseURI","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_projectDescription","type":"string"}],"name":"updateProjectDescription","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_index","type":"uint256"},{"internalType":"string","name":"_cidOrData","type":"string"},{"internalType":"enum IGenArt721CoreContractV3_Engine_Flex.ExternalAssetDependencyType","name":"_dependencyType","type":"uint8"}],"name":"updateProjectExternalAssetDependency","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_projectLicense","type":"string"}],"name":"updateProjectLicense","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint24","name":"_maxInvocations","type":"uint24"}],"name":"updateProjectMaxInvocations","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_projectName","type":"string"}],"name":"updateProjectName","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_scriptId","type":"uint256"},{"internalType":"string","name":"_script","type":"string"}],"name":"updateProjectScript","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"bytes32","name":"_scriptTypeAndVersion","type":"bytes32"}],"name":"updateProjectScriptType","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"uint256","name":"_secondMarketRoyalty","type":"uint256"}],"name":"updateProjectSecondaryMarketRoyaltyPercentage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_projectId","type":"uint256"},{"internalType":"string","name":"_projectWebsite","type":"string"}],"name":"updateProjectWebsite","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"renderProviderPrimarySalesPercentage_","type":"uint256"},{"internalType":"uint256","name":"platformProviderPrimarySalesPercentage_","type":"uint256"}],"name":"updateProviderPrimarySalesPercentages","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address payable","name":"_renderProviderPrimarySalesAddress","type":"address"},{"internalType":"address payable","name":"_renderProviderSecondarySalesAddress","type":"address"},{"internalType":"address payable","name":"_platformProviderPrimarySalesAddress","type":"address"},{"internalType":"address payable","name":"_platformProviderSecondarySalesAddress","type":"address"}],"name":"updateProviderSalesAddresses","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_renderProviderSecondarySalesBPS","type":"uint256"},{"internalType":"uint256","name":"_platformProviderSecondarySalesBPS","type":"uint256"}],"name":"updateProviderSecondarySalesBPS","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_randomizerAddress","type":"address"}],"name":"updateRandomizerAddress","outputs":[],"stateMutability":"nonpayable","type":"function"}]'

# Create contract object
#contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Set up the bot with the proper intents to read message content and reactions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

class MyView(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self):
        super().__init__(timeout=None)  # timeout of the view must be set to None

    @discord.ui.button(label="Artist", style=discord.ButtonStyle.primary)  # Create a button with the label "Artist" with color Blurple
    async def artist_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107785958746771538)
        await self.toggle_role(interaction, role)

    @discord.ui.button(label="Coder", style=discord.ButtonStyle.primary)  # Create a button with the label "Coder" with color Blurple
    async def coder_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107786089932013709)
        await self.toggle_role(interaction, role)

    @discord.ui.button(label="Collector", style=discord.ButtonStyle.primary)  # Create a button with the label "Collector" with color Blurple
    async def collector_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107786213575893012)
        await self.toggle_role(interaction, role)

    @staticmethod
    async def toggle_role(interaction, role):
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"I have successfully removed your {role.name} role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"I have successfully given you the {role.name} role.", ephemeral=True)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, id=1101580614945222708)
    channel = discord.utils.get(guild.channels, id=1129038551066103959)
    message_id = 1129129885928005874
    message = await channel.fetch_message(message_id)
    await message.edit(content="Tap the below buttons to add/remove the corresponding role:", view=MyView())
    while True:
        await track()
        await asyncio.sleep(60)

async def track():
    try:
        #Get our discord server and channels
        guild = discord.utils.get(bot.guilds, id=1101580614945222708)
        mint_channel = discord.utils.get(guild.channels, id=1126976550508712106)
        sales_channel = discord.utils.get(guild.channels, id=1126976977199435786)

        #Get the last events we already posted
        conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
        cur = conn.cursor()
        command = "select * from globalvariables where name = 'prohibition_latest_mint_hash'"
        cur.execute(command)
        results = cur.fetchall()
        latest_mint_hash = results[0][1]
        command = "select * from globalvariables where name = 'prohibition_latest_sale_hash'"
        cur.execute(command)
        results = cur.fetchall()
        latest_sale_hash = results[0][1]
        cur.close()
        conn.commit()
        conn.close()

        mints = []
        sales = []

        headers = {
            "accept": "*/*",
            "x-api-key": RESERVOIR_API_KEY
        }

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #If it's our first time through the loop, we leave off the continuation param
            if continuation == '':
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100"
            else:
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100&continuation="+continuation
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)

            #Go through all the transfers on the contract looking for ones coming from the 0x0 address (mint events)
            for i in data['transfers']:
                print(i['token']['name'])
                if i['price'] == None and i['from'] == '0x0000000000000000000000000000000000000000':
                    mint_hash = i['txHash']
                    #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                    if mint_hash == latest_mint_hash:
                        exit_flag = True
                        break
                    else:
                        mints.append(i)

            continuation = data['continuation']

            #We'll pause for a second so we don't get rate limited
            await asyncio.sleep(1)

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #If it's our first time through the loop, we leave off the continuation param
            if continuation == '':
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100"
            else:
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100&continuation="+continuation
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)

            #Go through all the transfers on the contract looking for ones that have a price associated with them (sale events)
            for i in data['transfers']:
                print(i['token']['name'])
                if i['price'] != None:
                    sale_hash = i['txHash']
                    #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                    if sale_hash == latest_sale_hash:
                        exit_flag = True
                        break
                    else:
                        sales.append(i)

            continuation = data['continuation']
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
        cur = conn.cursor()

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(mints):
            token_name = i['token']['name']
            timestamp = i['timestamp']
            image_url = i['token']['image']
            token_id = i['token']['tokenId']
            latest_mint_hash = i['txHash']
            embed = discord.Embed(title=token_name, description=f"{token_name} was minted at <t:{timestamp}:f>.\n\nhttps://prohibition.art/token/{token_id}")
            embed.set_image(url=image_url)
            await mint_channel.send(embed=embed)
            #Update our latest event so we know where we left off for next time
            command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_mint_hash'".format(latest_mint_hash)
            cur.execute(command)
            conn.commit()
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(sales):
            token_name = i['token']['name']
            timestamp = i['timestamp']
            image_url = i['token']['image']
            token_id = i['token']['tokenId']
            price_symbol = i['price']['currency']['symbol']
            price_amount = i['price']['amount']['decimal']
            latest_sale_hash = i['txHash']
            embed = discord.Embed(title=token_name, description=f"{token_name} sold for {price_amount} {price_symbol} at <t:{timestamp}:f>.\n\nhttps://prohibition.art/token/{token_id}")
            embed.set_image(url=image_url)
            await sales_channel.send(embed=embed)
            #Update our latest event so we know where we left off for next time
            command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_sale_hash'".format(latest_sale_hash)
            cur.execute(command)
            conn.commit()
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        cur.close()
        conn.commit()
        conn.close()

    #If an error occurs, we're gonna log it and pause for a minute, then try again
    except Exception as e:
        print(f"An error occurred: {e}")
        await asyncio.sleep(60)

bot.run(BOT_TOKEN)
