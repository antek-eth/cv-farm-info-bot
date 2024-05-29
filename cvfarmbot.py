import logging
import json
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3
import time

# Import formatting functions
from formatting import format_profile_data

# Load environment variables
load_dotenv()
WEB3_PROVIDER_URL = os.getenv('WEB3_PROVIDER_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))

# Load seed information from a JSON file
with open('seeds.json', 'r') as file:
    seed_dict = json.load(file)  # Directly load the dictionary

# Load contract configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Helper function to load ABI and get contract instance
def get_contract_instance(config_item):
    with open(config_item['abi_file'], 'r') as abi_file:
        abi = json.load(abi_file)
    return w3.eth.contract(address=config_item['address'], abi=abi)

# Initialize contract instances
profile_contract = get_contract_instance(config['contracts']['profile'])
balance_contract = get_contract_instance(config['contracts']['balance'])
farmer_contract = get_contract_instance(config['contracts']['farmer'])

def get_profile(contract, address):
    profile_tuple = contract.functions.getProfile(address).call()
    profile_keys = [
        "playerName", "referral", "referralCode", "profilePictureId", 
        "exp", "farmLevel", "profileHarvestBonus", "lockedBalance", 
        "freeFeebleRolls", "freePicoRolls", "freeSeedRolls", 
        "freePremiumSeedRolls", "claimedSage", "claimedWage"
    ]
    profile_dict = dict(zip(profile_keys, profile_tuple))
    profile_dict['wallet_address'] = address  # Ensure wallet address is added here
    return profile_dict

def get_balance(contract, address):
    balance_wei = contract.functions.balanceOf(address).call()
    balance_ether = w3.from_wei(balance_wei, 'ether')  # Convert from Wei to Ether
    return f"{balance_ether:.2f}"  # Format the float to two decimal places


def get_farmer_info(contract, address):
    # Assuming the function returns a tuple where the first item is the list of plots
    plots_info = contract.functions.getFarmerInfo(address).call()
    return {'plots': plots_info[0], 'pending_rewards': plots_info[1]}

async def address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = update.message.text
    if wallet_address.startswith('0x') and len(wallet_address) == 42:
        try:
            profile = get_profile(profile_contract, wallet_address)
            balance = get_balance(balance_contract, wallet_address)
            farmer_info = get_farmer_info(farmer_contract, wallet_address)
            # Merge the profile and balance data correctly before passing
            profile['balance'] = balance  # Add balance to the profile dictionary
            formatted_profile = format_profile_data(profile, farmer_info, seed_dict)
            await update.message.reply_text(formatted_profile)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            await update.message.reply_text('Failed to retrieve data. Please try again.')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Welcome to the bot. Please send your wallet address to get started.')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, address))
    application.run_polling()

if __name__ == "__main__":
    main()
