import logging
import datetime
import time
from tabulate import tabulate

# Set up basic logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_total_plots_by_level(level):
    if level <= 3:
        return 15
    elif level <= 5:
        return 17
    elif level <= 7:
        return 18
    elif level <= 11:
        return 19
    elif level <= 14:
        return 20
    else:
        return 21

def calculate_time_left(life_seconds, plant_timestamp):
    current_time = int(time.time())
    harvest_time = plant_timestamp + life_seconds
    seconds_left = harvest_time - current_time
    if seconds_left > 0:
        return str(datetime.timedelta(seconds=seconds_left))
    else:
        return "Ready"

def get_seconds_left(life_seconds, plant_timestamp):
    current_time = int(time.time())
    harvest_time = plant_timestamp + life_seconds
    return max(harvest_time - current_time, 0)

def format_profile_data(profile_data, farmer_info, seed_dict):
    farm_level = profile_data['farmLevel']
    total_plots = get_total_plots_by_level(farm_level)
    plots_used = sum(1 for plot in farmer_info['plots'] if plot[0] != 0)

    table_data = []

    min_time_left = float('inf')
    next_harvest = "No crops planted."

    for idx, plot in enumerate(farmer_info['plots']):
        crop_id, plant_timestamp, _ = plot
        crop_id_str = str(crop_id)  # Explicitly convert crop_id to string
        if crop_id_str in seed_dict:
            seed = seed_dict[crop_id_str]
            time_left = calculate_time_left(seed['life'], plant_timestamp)
            seconds_left = get_seconds_left(seed['life'], plant_timestamp)
            if seconds_left < min_time_left:
                min_time_left = seconds_left
                next_harvest = time_left
            table_data.append([seed['name'], time_left, seed['rarity']])
        else:
            logger.warning(f"Seed data not found for crop_id {crop_id}")

    headers = ["Crop", "Time Left", "Rarity"]
    table = tabulate(table_data, headers, tablefmt="pipe")

    formatted_data = (
        f"🚜 Farm Report: {profile_data['wallet_address'][:5]}...{profile_data['wallet_address'][-4:]}\n"
        f"🏆 Farm Level: {farm_level}\n"
        f"💵 Balance: {profile_data['balance']} YIELD\n"
        f"Plots: {plots_used}/{total_plots}\n"
        f"{table}\n"
        f"🌾 Next Harvest: {next_harvest}\n"
    )

    logger.info("Finished profile formatting")
    return formatted_data
