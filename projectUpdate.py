from web3 import Web3, HTTPProvider
import requests
import time
import json
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

prohibitionContract = "0x47A91457a3a1f700097199Fd63c039c4784384aB"
ALCHEMY_MAINNET_API_KEY = os.environ.get('ALCHEMY_MAINNET_API_KEY')
ARBISCAN_API_KEY = os.environ.get('ARBISCAN_API_KEY')
DATABASETOKEN = os.environ.get('DATABASETOKEN')

#Get the prohibition contract ABI
response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + prohibitionContract + "&apikey=" + ARBISCAN_API_KEY)
PROHIBITION_CONTRACT_ABI = json.loads(response.text)['result']

#Connect to alchemy
w3 = Web3(HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/'+ALCHEMY_MAINNET_API_KEY))

#Load the prohibition contract
contract = w3.eth.contract(address=prohibitionContract, abi=PROHIBITION_CONTRACT_ABI)

#See how many projects currently exist
nextProjectId = contract.functions.nextProjectId().call()

#Connect to Postgres
conn = psycopg2.connect(DATABASETOKEN, sslmode='require')
cur = conn.cursor()

#Go through all the existing projects
for projectID in range(0,nextProjectId):
    #Grab some pertinent info from the projectStateData function
    result = contract.functions.projectStateData(projectID).call()
    #Extract the returned values
    invocations, maxInvocations, active, paused, completedTimestamp, locked = result
    #If the project isn't active, we don't need to worry about it
    if active:
        #Grab some more info from the projectDetails function
        result = contract.functions.projectDetails(projectID).call()
        #Extract the returned values
        projectName, artist, description, website, license = result
        #Get the prohibition minter contract address
        minterContractAddress = contract.functions.minterContract().call()
        #Get the minter contract ABI
        response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + minterContractAddress + "&apikey=" + ARBISCAN_API_KEY)
        minterContractABI = json.loads(response.text)['result']
        #Load the minter contract
        minterContract = w3.eth.contract(address=minterContractAddress, abi=minterContractABI)
        #Now get this specific project's minter contract address
        projectMinterContractAddress = minterContract.functions.getMinterForProject(projectID).call()
        #Get the project's minter contract ABI
        response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + projectMinterContractAddress + "&apikey=" + ARBISCAN_API_KEY)
        projectMinterContractABI = json.loads(response.text)['result']
        #Load the project's minter contract
        projectMinterContract = w3.eth.contract(address=projectMinterContractAddress, abi=projectMinterContractABI)
        #Get a few more pieces of info from the getPriceInfo function on the minter contract
        result = projectMinterContract.functions.getPriceInfo(projectID).call()
        #Extract the returned values
        isConfigured, tokenPriceInWei, currencySymbol, currencyAddress = result
        #Convert the token price into standard readable format
        readableTokenPrice = float(tokenPriceInWei)/1000000000000000000
        #Set the project url and image url
        projectImage = "https://prohibition-arbitrum.s3.amazonaws.com/" + str(projectID * 1000000) + ".png"
        url = "https://prohibition.art/api/project/0x47A91457a3a1f700097199Fd63c039c4784384aB-"+str(projectID)
        response = requests.get(url)
        #Make sure the project exists on the prohibition platform
        if response.text == '{"code":"NOT_FOUND","error":"Project not found"}':
            continue
        data = json.loads(response.text)
        projectURL = "https://prohibition.art/project/" + data['slug']

        #See if there are still tokens available to mint
        stillMinting = True
        if invocations >= maxInvocations:
            stillMinting = False
        #Upsert the SQL table
        cur.execute("""
            INSERT INTO prohibition_projects (
                project_ID, 
                is_active, 
                invocations, 
                max_invocations, 
                project_name, 
                project_artist, 
                minter_contract, 
                project_price, 
                project_image, 
                project_url
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (project_ID) 
            DO UPDATE SET 
                is_active = EXCLUDED.is_active,
                invocations = EXCLUDED.invocations,
                max_invocations = EXCLUDED.max_invocations,
                project_name = EXCLUDED.project_name,
                project_artist = EXCLUDED.project_artist,
                minter_contract = EXCLUDED.minter_contract,
                project_price = EXCLUDED.project_price,
                project_image = EXCLUDED.project_image,
                project_url = EXCLUDED.project_url;
        """, (projectID, stillMinting, invocations, maxInvocations, projectName, artist, projectMinterContractAddress, readableTokenPrice, projectImage, projectURL))
        conn.commit()
        
cur.close()
conn.commit()
conn.close()
