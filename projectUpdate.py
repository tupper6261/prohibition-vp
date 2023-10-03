from web3 import Web3, HTTPProvider
import requests
import time
import json
import psycopg2

prohibitionContract = "0x47A91457a3a1f700097199Fd63c039c4784384aB"
ALCHEMY_MAINNET_API_KEY = "2DTzGsHNcWmQi03oUKEsKtdQt7ON5p7A"
ARBISCAN_API_KEY = "11P4BF36JQ73IG7GV69QM428U15AWMFRK1"
DATABASETOKEN = "postgres://yezaufigplmbrj:daa40d1942c2a9bc98258d57d3c6835b989d25aae748cfb199526dca7da06a66@ec2-34-228-248-175.compute-1.amazonaws.com:5432/db6a6eqkldihes"

response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + prohibitionContract + "&apikey=" + ARBISCAN_API_KEY)
PROHIBITION_CONTRACT_ABI = json.loads(response.text)['result']

w3 = Web3(HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/'+ALCHEMY_MAINNET_API_KEY))

contract = w3.eth.contract(address=prohibitionContract, abi=PROHIBITION_CONTRACT_ABI)

nextProjectId = contract.functions.nextProjectId().call()

conn = psycopg2.connect(DATABASETOKEN, sslmode='require')
cur = conn.cursor()

for projectID in range(0,nextProjectId):
    
    result = contract.functions.projectStateData(projectID).call()

    # Extract the returned values
    invocations, maxInvocations, active, paused, completedTimestamp, locked = result

    if active:
        result = contract.functions.projectDetails(projectID).call()

        projectName, artist, description, website, license = result

        minterContractAddress = contract.functions.minterContract().call()

        response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + minterContractAddress + "&apikey=" + ARBISCAN_API_KEY)
        minterContractABI = json.loads(response.text)['result']

        minterContract = w3.eth.contract(address=minterContractAddress, abi=minterContractABI)

        projectMinterContractAddress = minterContract.functions.getMinterForProject(projectID).call()

        response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + projectMinterContractAddress + "&apikey=" + ARBISCAN_API_KEY)
        projectMinterContractABI = json.loads(response.text)['result']

        projectMinterContract = w3.eth.contract(address=projectMinterContractAddress, abi=projectMinterContractABI)

        result = projectMinterContract.functions.getPriceInfo(projectID).call()

        isConfigured, tokenPriceInWei, currencySymbol, currencyAddress = result

        readableTokenPrice = float(tokenPriceInWei)/1000000000000000000

        projectImage = "https://prohibition-arbitrum.s3.amazonaws.com/" + str(projectID * 1000000) + ".png"
        url = "https://prohibition.art/api/project/0x47A91457a3a1f700097199Fd63c039c4784384aB-"+str(projectID)
        response = requests.get(url)
        if response.text == '{"code":"NOT_FOUND","error":"Project not found"}':
            continue
        data = json.loads(response.text)
        projectURL = "https://prohibition.art/project/" + data['slug']

        stillMinting = True
        if invocations >= maxInvocations:
            stillMinting = False

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
        
        print (projectName)
        print (projectID)
        print (str(invocations) + "/" + str(maxInvocations))
        print (str(readableTokenPrice) + currencySymbol)
        print (projectImage)
        print (projectURL)
        print ("-----")
        
cur.close()
conn.commit()
conn.close()
