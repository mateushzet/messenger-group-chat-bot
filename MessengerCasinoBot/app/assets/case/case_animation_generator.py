import os
import random
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import logging
from PIL import ImageFilter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SkinPriceRepository:

    SKIN_DATA = [       

        ('AK-47 Wasteland Rebel', 'Factory New', 'No', 184, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Minimal Wear', 'No', 45, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Field-Tested', 'No', 27, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Well-Worn', 'No', 35, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Battle-Scarred', 'No', 26, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Factory New', 'StatTrak', 1054, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Minimal Wear', 'StatTrak', 120, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Field-Tested', 'StatTrak', 88, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Well-Worn', 'StatTrak', 100, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Battle-Scarred', 'StatTrak', 99, (235, 75, 75)),

        ('AWP Asiimov', 'Field-Tested', 'No', 133, (235, 75, 75)),
        ('AWP Asiimov', 'Well-Worn', 'No', 100, (235, 75, 75)),
        ('AWP Asiimov', 'Battle-Scarred', 'No', 72, (235, 75, 75)),
        ('AWP Asiimov', 'Field-Tested', 'StatTrak', 225, (235, 75, 75)),
        ('AWP Asiimov', 'Well-Worn', 'StatTrak', 165, (235, 75, 75)),
        ('AWP Asiimov', 'Battle-Scarred', 'StatTrak', 122, (235, 75, 75)),

        ('AUG Chameleon', 'Factory New', 'No', 4, (235, 75, 75)),
        ('AUG Chameleon', 'Minimal Wear', 'No', 2, (235, 75, 75)),
        ('AUG Chameleon', 'Field-Tested', 'No', 2, (235, 75, 75)),
        ('AUG Chameleon', 'Well-Worn', 'No', 3, (235, 75, 75)),
        ('AUG Chameleon', 'Battle-Scarred', 'No', 3, (235, 75, 75)),
        ('AUG Chameleon', 'Factory New', 'StatTrak', 15, (235, 75, 75)),
        ('AUG Chameleon', 'Minimal Wear', 'StatTrak', 8, (235, 75, 75)),
        ('AUG Chameleon', 'Field-Tested', 'StatTrak', 7, (235, 75, 75)),
        ('AUG Chameleon', 'Well-Worn', 'StatTrak', 9, (235, 75, 75)),
        ('AUG Chameleon', 'Battle-Scarred', 'StatTrak', 9, (235, 75, 75)),

        ('AK-47 Redline', 'Minimal Wear', 'No', 147, (211, 44, 230)),
        ('AK-47 Redline', 'Field-Tested', 'No', 28, (211, 44, 230)),
        ('AK-47 Redline', 'Well-Worn', 'No', 21, (211, 44, 230)),
        ('AK-47 Redline', 'Battle-Scarred', 'No', 19, (211, 44, 230)),
        ('AK-47 Redline', 'Minimal Wear', 'StatTrak', 310, (211, 44, 230)),
        ('AK-47 Redline', 'Field-Tested', 'StatTrak', 72, (211, 44, 230)),
        ('AK-47 Redline', 'Well-Worn', 'StatTrak', 43, (211, 44, 230)),
        ('AK-47 Redline', 'Battle-Scarred', 'StatTrak', 35, (211, 44, 230)),

        ('SG 553 Pulse', 'Minimal Wear', 'No', 5, (136, 71, 255)),
        ('SG 553 Pulse', 'Field-Tested', 'No', 3, (136, 71, 255)),
        ('SG 553 Pulse', 'Well-Worn', 'No', 2, (136, 71, 255)),
        ('SG 553 Pulse', 'Battle-Scarred', 'No', 2, (136, 71, 255)),
        ('SG 553 Pulse', 'Minimal Wear', 'StatTrak', 10, (136, 71, 255)),
        ('SG 553 Pulse', 'Field-Tested', 'StatTrak', 5, (136, 71, 255)),
        ('SG 553 Pulse', 'Well-Worn', 'StatTrak', 4, (136, 71, 255)),
        ('SG 553 Pulse', 'Battle-Scarred', 'StatTrak', 5, (136, 71, 255)),

        ('USP-S Guardian', 'Factory New', 'No', 7, (136, 71, 255)),
        ('USP-S Guardian', 'Minimal Wear', 'No', 5, (136, 71, 255)),
        ('USP-S Guardian', 'Field-Tested', 'No', 3, (136, 71, 255)),
        ('USP-S Guardian', 'Factory New', 'StatTrak', 13, (136, 71, 255)),
        ('USP-S Guardian', 'Minimal Wear', 'StatTrak', 9, (136, 71, 255)),
        ('USP-S Guardian', 'Field-Tested', 'StatTrak', 9, (136, 71, 255)),

        ('MAG-7 Heaven Guard', 'Factory New', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Minimal Wear', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Field-Tested', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Well-Worn', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Factory New', 'StatTrak', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Minimal Wear', 'StatTrak', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Field-Tested', 'StatTrak', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Well-Worn', 'StatTrak', 2, (75, 105, 255)),

        ('M4A4 Griffin', 'Factory New', 'No', 6, (136, 71, 255)),
        ('M4A4 Griffin', 'Minimal Wear', 'No', 3, (136, 71, 255)),
        ('M4A4 Griffin', 'Field-Tested', 'No', 2, (136, 71, 255)),
        ('M4A4 Griffin', 'Well-Worn', 'No', 3, (136, 71, 255)),
        ('M4A4 Griffin', 'Battle-Scarred', 'No', 2, (136, 71, 255)),
        ('M4A4 Griffin', 'Factory New', 'StatTrak', 16, (136, 71, 255)),
        ('M4A4 Griffin', 'Minimal Wear', 'StatTrak', 7, (136, 71, 255)),
        ('M4A4 Griffin', 'Field-Tested', 'StatTrak', 5, (136, 71, 255)),
        ('M4A4 Griffin', 'Well-Worn', 'StatTrak', 7, (136, 71, 255)),
        ('M4A4 Griffin', 'Battle-Scarred', 'StatTrak', 5, (136, 71, 255)),

        ('Tec-9 Sandstorm', 'Minimal Wear', 'No', 2, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Field-Tested', 'No', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Well-Worn', 'No', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Battle-Scarred', 'No', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Minimal Wear', 'StatTrak', 3, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Field-Tested', 'StatTrak', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Well-Worn', 'StatTrak', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Battle-Scarred', 'StatTrak', 1, (75, 105, 255)),

        ('P2000 Fire Elemental', 'Factory New', 'No', 21, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Minimal Wear', 'No', 11, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Field-Tested', 'No', 9, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Well-Worn', 'No', 10, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Battle-Scarred', 'No', 8, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Factory New', 'StatTrak', 138, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Minimal Wear', 'StatTrak', 64, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Field-Tested', 'StatTrak', 40, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Well-Worn', 'StatTrak', 63, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Battle-Scarred', 'StatTrak', 50, (235, 75, 75)),

        ('M4A1-S Cyrex', 'Factory New', 'No', 39,  (235, 75, 75)),
        ('M4A1-S Cyrex', 'Minimal Wear', 'No', 28, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Field-Tested', 'No', 19, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Well-Worn', 'No', 20, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Battle-Scarred', 'No', 18, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Factory New', 'StatTrak', 118, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Minimal Wear', 'StatTrak', 87, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Field-Tested', 'StatTrak', 50, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Well-Worn', 'StatTrak', 53, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Battle-Scarred', 'StatTrak', 58, (235, 75, 75)),

        ('P90 Asiimov', 'Factory New', 'No', 30, (235, 75, 75)),
        ('P90 Asiimov', 'Minimal Wear', 'No', 13, (235, 75, 75)),
        ('P90 Asiimov', 'Field-Tested', 'No', 6, (235, 75, 75)),
        ('P90 Asiimov', 'Well-Worn', 'No', 6, (235, 75, 75)),
        ('P90 Asiimov', 'Battle-Scarred', 'No', 6, (235, 75, 75)),
        ('P90 Asiimov', 'Factory New', 'StatTrak', 161, (235, 75, 75)),
        ('P90 Asiimov', 'Minimal Wear', 'StatTrak', 49, (235, 75, 75)),
        ('P90 Asiimov', 'Field-Tested', 'StatTrak', 24, (235, 75, 75)),
        ('P90 Asiimov', 'Well-Worn', 'StatTrak', 20, (235, 75, 75)),
        ('P90 Asiimov', 'Battle-Scarred', 'StatTrak', 22, (235, 75, 75)),

        ('Glock-18 Water Elemental', 'Factory New', 'No', 11, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Minimal Wear', 'No', 7, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Field-Tested', 'No', 4, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Well-Worn', 'No', 4, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Battle-Scarred', 'No', 4, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Factory New', 'StatTrak', 45, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Minimal Wear', 'StatTrak', 25, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Field-Tested', 'StatTrak', 15, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Well-Worn', 'StatTrak', 18, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Battle-Scarred', 'StatTrak', 15, (211, 44, 230)),

        ('CZ75-Auto Tigris', 'Factory New', 'No', 2, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Minimal Wear', 'No', 1, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Field-Tested', 'No', 1, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Well-Worn', 'No', 1, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Battle-Scarred', 'No', 1, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Factory New', 'StatTrak', 4, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Minimal Wear', 'StatTrak', 2, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Field-Tested', 'StatTrak', 1, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Well-Worn', 'StatTrak', 1, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Battle-Scarred', 'StatTrak', 1, (136, 71, 255)),

        ('PP-Bizon Osiris', 'Factory New', 'No', 1, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Minimal Wear', 'No', 1, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Field-Tested', 'No', 1, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Well-Worn', 'No', 1, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Battle-Scarred', 'No', 1, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Factory New', 'StatTrak', 4, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Minimal Wear', 'StatTrak', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Field-Tested', 'StatTrak', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Well-Worn', 'StatTrak', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Battle-Scarred', 'StatTrak', 1, (136, 71, 255)),

        ('Nova Koi', 'Factory New', 'No', 1, (136, 71, 255)),
        ('Nova Koi', 'Minimal Wear', 'No', 1, (136, 71, 255)),
        ('Nova Koi', 'Field-Tested', 'No', 1, (136, 71, 255)),
        ('Nova Koi', 'Factory New', 'StatTrak', 4, (136, 71, 255)),
        ('Nova Koi', 'Minimal Wear', 'StatTrak', 2, (136, 71, 255)),
        ('Nova Koi', 'Field-Tested', 'StatTrak', 2, (136, 71, 255)),

        ('MP7 Urban Hazard', 'Factory New', 'No', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Minimal Wear', 'No', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Field-Tested', 'No', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Well-Worn', 'No', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Battle-Scarred', 'No', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Factory New', 'StatTrak', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Minimal Wear', 'StatTrak', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Field-Tested', 'StatTrak', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Well-Worn', 'StatTrak', 1, (75, 105, 255)),
        ('MP7 Urban Hazard', 'Battle-Scarred', 'StatTrak', 1, (75, 105, 255)),

        ('SSG 08 Abyss', 'Factory New', 'No', 2, (75, 105, 255)),
        ('SSG 08 Abyss', 'Minimal Wear', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Field-Tested', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Well-Worn', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Battle-Scarred', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Factory New', 'StatTrak', 9, (75, 105, 255)),
        ('SSG 08 Abyss', 'Minimal Wear', 'StatTrak', 2, (75, 105, 255)),
        ('SSG 08 Abyss', 'Field-Tested', 'StatTrak', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Well-Worn', 'StatTrak', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Battle-Scarred', 'StatTrak', 1, (75, 105, 255)),

        ('M4A1-S Bright Water', 'Minimal Wear', 'No', 27, (136, 71, 255)),
        ('M4A1-S Bright Water', 'Field-Tested', 'No', 27, (136, 71, 255)),
        ('M4A1-S Bright Water', 'Minimal Wear', 'StatTrak', 69, (136, 71, 255)),
        ('M4A1-S Bright Water', 'Field-Tested', 'StatTrak', 62, (136, 71, 255)),

        ('AK-47 Fire Serpent', 'Factory New', 'No', 2143,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Minimal Wear', 'No', 1125,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Field-Tested', 'No', 774,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Well-Worn', 'No', 703,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Battle-Scarred', 'No', 469,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Factory New', 'StatTrak', 4436,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Minimal Wear', 'StatTrak', 2744,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Field-Tested', 'StatTrak', 1672,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Well-Worn', 'StatTrak', 1293,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Battle-Scarred', 'StatTrak', 1012,(235, 75, 75)),

        ('AK-47 Vulcan', 'Factory New', 'No', 706,(235, 75, 75)),
        ('AK-47 Vulcan', 'Minimal Wear', 'No', 443,(235, 75, 75)),
        ('AK-47 Vulcan', 'Field-Tested', 'No', 226,(235, 75, 75)),
        ('AK-47 Vulcan', 'Well-Worn', 'No', 148,(235, 75, 75)),
        ('AK-47 Vulcan', 'Battle-Scarred', 'No', 136,(235, 75, 75)),
        ('AK-47 Vulcan', 'Factory New', 'StatTrak', 1317,(235, 75, 75)),
        ('AK-47 Vulcan', 'Minimal Wear', 'StatTrak', 785,(235, 75, 75)),
        ('AK-47 Vulcan', 'Field-Tested', 'StatTrak', 349,(235, 75, 75)),
        ('AK-47 Vulcan', 'Well-Worn', 'StatTrak', 226,(235, 75, 75)),
        ('AK-47 Vulcan', 'Battle-Scarred', 'StatTrak', 162,(235, 75, 75)),

        ('AUG Torque', 'Factory New', 'No', 9,(136, 71, 255)),
        ('AUG Torque', 'Minimal Wear', 'No', 9,(136, 71, 255)),
        ('AUG Torque', 'Field-Tested', 'No', 8,(136, 71, 255)),
        ('AUG Torque', 'Well-Worn', 'No', 7,(136, 71, 255)),
        ('AUG Torque', 'Battle-Scarred', 'No', 7,(136, 71, 255)),
        ('AUG Torque', 'Factory New', 'StatTrak', 16,(136, 71, 255)),
        ('AUG Torque', 'Minimal Wear', 'StatTrak', 13,(136, 71, 255)),
        ('AUG Torque', 'Field-Tested', 'StatTrak', 10,(136, 71, 255)),
        ('AUG Torque', 'Well-Worn', 'StatTrak', 11,(136, 71, 255)),
        ('AUG Torque', 'Battle-Scarred', 'StatTrak', 11,(136, 71, 255)),

        ('Tec-9 Isaac', 'Factory New', 'No', 11,(75, 105, 255)),
        ('Tec-9 Isaac', 'Minimal Wear', 'No', 4,(75, 105, 255)),
        ('Tec-9 Isaac', 'Field-Tested', 'No', 3,(75, 105, 255)),
        ('Tec-9 Isaac', 'Well-Worn', 'No', 2,(75, 105, 255)),
        ('Tec-9 Isaac', 'Battle-Scarred', 'No', 2,(75, 105, 255)),
        ('Tec-9 Isaac', 'Factory New', 'StatTrak', 26,(75, 105, 255)),
        ('Tec-9 Isaac', 'Minimal Wear', 'StatTrak', 6,(75, 105, 255)),
        ('Tec-9 Isaac', 'Field-Tested', 'StatTrak', 3,(75, 105, 255)),
        ('Tec-9 Isaac', 'Well-Worn', 'StatTrak', 2,(75, 105, 255)),
        ('Tec-9 Isaac', 'Battle-Scarred', 'StatTrak', 2,(75, 105, 255)),

        ('P90 Module', 'Factory New', 'No', 2,(75, 105, 255)),
        ('P90 Module', 'Minimal Wear', 'No', 2,(75, 105, 255)),
        ('P90 Module', 'Field-Tested', 'No', 2,(75, 105, 255)),
        ('P90 Module', 'Factory New', 'StatTrak', 3,(75, 105, 255)),
        ('P90 Module', 'Minimal Wear', 'StatTrak', 2,(75, 105, 255)),
        ('P90 Module', 'Field-Tested', 'StatTrak', 2,(75, 105, 255)),

        ('P2000 Pulse', 'Factory New', 'No', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Minimal Wear', 'No', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Field-Tested', 'No', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Well-Worn', 'No', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Battle-Scarred', 'No', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Factory New', 'StatTrak', 3,(75, 105, 255)),
        ('P2000 Pulse', 'Minimal Wear', 'StatTrak', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Field-Tested', 'StatTrak', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Well-Worn', 'StatTrak', 2,(75, 105, 255)),
        ('P2000 Pulse', 'Battle-Scarred', 'StatTrak', 1,(75, 105, 255)),

        ('SSG 08 Slashed', 'Field-Tested', 'No', 2,(75, 105, 255)),
        ('SSG 08 Slashed', 'Well-Worn', 'No', 1,(75, 105, 255)),
        ('SSG 08 Slashed', 'Battle-Scarred', 'No', 2,(75, 105, 255)),
        ('SSG 08 Slashed', 'Field-Tested', 'StatTrak', 2,(75, 105, 255)),
        ('SSG 08 Slashed', 'Well-Worn', 'StatTrak', 2,(75, 105, 255)),
        ('SSG 08 Slashed', 'Battle-Scarred', 'StatTrak', 2,(75, 105, 255)),

        ('AK-47 Aquamarine Revenge', 'Factory New', 'No', 121,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Minimal Wear', 'No', 64,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Field-Tested', 'No', 32,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Well-Worn', 'No', 20,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Battle-Scarred', 'No', 21,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Factory New', 'StatTrak', 217,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Minimal Wear', 'StatTrak', 124,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Field-Tested', 'StatTrak', 74,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Well-Worn', 'StatTrak', 51,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Battle-Scarred', 'StatTrak', 49,(235, 75, 75)),

        ('AWP Hyper Beast', 'Factory New', 'No', 81,(235, 75, 75)),
        ('AWP Hyper Beast', 'Minimal Wear', 'No', 42,(235, 75, 75)),
        ('AWP Hyper Beast', 'Field-Tested', 'No', 23,(235, 75, 75)),
        ('AWP Hyper Beast', 'Well-Worn', 'No', 21,(235, 75, 75)),
        ('AWP Hyper Beast', 'Battle-Scarred', 'No', 20,(235, 75, 75)),
        ('AWP Hyper Beast', 'Factory New', 'StatTrak', 210,(235, 75, 75)),
        ('AWP Hyper Beast', 'Minimal Wear', 'StatTrak', 104,(235, 75, 75)),
        ('AWP Hyper Beast', 'Field-Tested', 'StatTrak', 58,(235, 75, 75)),
        ('AWP Hyper Beast', 'Well-Worn', 'StatTrak', 54,(235, 75, 75)),
        ('AWP Hyper Beast', 'Battle-Scarred', 'StatTrak', 54,(235, 75, 75)),

        ('M4A4 Evil Daimyo', 'Factory New', 'No', 5,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Minimal Wear', 'No', 3,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Field-Tested', 'No', 2,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Well-Worn', 'No', 2,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Battle-Scarred', 'No', 1,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Factory New', 'StatTrak', 15,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Minimal Wear', 'StatTrak', 8,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Field-Tested', 'StatTrak', 5,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Well-Worn', 'StatTrak', 6,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Battle-Scarred', 'StatTrak', 5,(136, 71, 255)),

        ('USP-S Torque', 'Factory New', 'No', 2,(75, 105, 255)),
        ('USP-S Torque', 'Minimal Wear', 'No', 1,(75, 105, 255)),
        ('USP-S Torque', 'Field-Tested', 'No', 1,(75, 105, 255)),
        ('USP-S Torque', 'Well-Worn', 'No', 1,(75, 105, 255)),
        ('USP-S Torque', 'Battle-Scarred', 'No', 1,(75, 105, 255)),
        ('USP-S Torque', 'Factory New', 'StatTrak', 4,(75, 105, 255)),
        ('USP-S Torque', 'Minimal Wear', 'StatTrak', 3,(75, 105, 255)),
        ('USP-S Torque', 'Field-Tested', 'StatTrak', 2,(75, 105, 255)),
        ('USP-S Torque', 'Well-Worn', 'StatTrak', 2,(75, 105, 255)),
        ('USP-S Torque', 'Battle-Scarred', 'StatTrak', 3,(75, 105, 255)),

        ('Karambit Safari Mesh', 'Factory New', 'No', 823,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Minimal Wear', 'No', 586,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Field-Tested', 'No', 559,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Well-Worn', 'No', 541,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Battle-Scarred', 'No', 569,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Minimal Wear', 'StatTrak', 576,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Field-Tested', 'StatTrak', 563,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Well-Worn', 'StatTrak', 583,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Battle-Scarred', 'StatTrak', 562,(255, 215, 0)),

        ('Butterfly Knife Fade', 'Factory New', 'No', 3372,(255, 215, 0)),
        ('Butterfly Knife Fade', 'Minimal Wear', 'No', 3000,(255, 215, 0)),
        ('Butterfly Knife Fade', 'Factory New', 'StatTrak', 3156,(255, 215, 0)),
        ('Butterfly Knife Fade', 'Minimal Wear', 'StatTrak', 3238,(255, 215, 0)),

        ('Butterfly Knife Ultraviolet', 'Factory New', 'No', 2150,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Minimal Wear', 'No', 1146,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Field-Tested', 'No', 939,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Well-Worn', 'No', 878,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Battle-Scarred', 'No', 772,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Factory New', 'StatTrak', 6000,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Minimal Wear', 'StatTrak', 1130,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Field-Tested', 'StatTrak', 892,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Well-Worn', 'StatTrak', 864,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Battle-Scarred', 'StatTrak', 768,(255, 215, 0)),

        ('Bayonet Slaughter', 'Factory New', 'No', 541,(255, 215, 0)),
        ('Bayonet Slaughter', 'Minimal Wear', 'No', 450,(255, 215, 0)),
        ('Bayonet Slaughter', 'Field-Tested', 'No', 400,(255, 215, 0)),
        ('Bayonet Slaughter', 'Factory New', 'StatTrak', 590,(255, 215, 0)),
        ('Bayonet Slaughter', 'Minimal Wear', 'StatTrak', 543,(255, 215, 0)),
        ('Bayonet Slaughter', 'Field-Tested', 'StatTrak', 429,(255, 215, 0)),

        ('Bayonet Urban Masked', 'Factory New', 'No', 337,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Minimal Wear', 'No', 226,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Field-Tested', 'No', 190,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Well-Worn', 'No', 186,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Battle-Scarred', 'No', 185,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Minimal Wear', 'StatTrak', 240,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Field-Tested', 'StatTrak', 196,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Well-Worn', 'StatTrak', 192,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Battle-Scarred', 'StatTrak', 192,(255, 215, 0)),

        ('Falchion Knife Case Hardened', 'Factory New', 'No', 356,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Minimal Wear', 'No', 239,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Field-Tested', 'No', 209,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Well-Worn', 'No', 180,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Battle-Scarred', 'No', 165,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Factory New', 'StatTrak', 412,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Minimal Wear', 'StatTrak', 274,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Field-Tested', 'StatTrak', 240,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Well-Worn', 'StatTrak', 206,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Battle-Scarred', 'StatTrak', 218,(255, 215, 0)),

        ('Gut Knife Freehand', 'Factory New', 'No', 121,(255, 215, 0)),
        ('Gut Knife Freehand', 'Minimal Wear', 'No', 119,(255, 215, 0)),
        ('Gut Knife Freehand', 'Field-Tested', 'No', 116,(255, 215, 0)),
        ('Gut Knife Freehand', 'Well-Worn', 'No', 115,(255, 215, 0)),
        ('Gut Knife Freehand', 'Battle-Scarred', 'No', 109,(255, 215, 0)),
        ('Gut Knife Freehand', 'Factory New', 'StatTrak', 145,(255, 215, 0)),
        ('Gut Knife Freehand', 'Minimal Wear', 'StatTrak', 122,(255, 215, 0)),
        ('Gut Knife Freehand', 'Field-Tested', 'StatTrak', 117,(255, 215, 0)),
        ('Gut Knife Freehand', 'Well-Worn', 'StatTrak', 154,(255, 215, 0)),
        ('Gut Knife Freehand', 'Battle-Scarred', 'StatTrak', 343,(255, 215, 0)),

        ('Flip Knife Lore', 'Factory New', 'No', 439,(255, 215, 0)),
        ('Flip Knife Lore', 'Minimal Wear', 'No', 335,(255, 215, 0)),
        ('Flip Knife Lore', 'Field-Tested', 'No', 269,(255, 215, 0)),
        ('Flip Knife Lore', 'Well-Worn', 'No', 260,(255, 215, 0)),
        ('Flip Knife Lore', 'Battle-Scarred', 'No', 229,(255, 215, 0)),
        ('Flip Knife Lore', 'Factory New', 'StatTrak', 438,(255, 215, 0)),
        ('Flip Knife Lore', 'Minimal Wear', 'StatTrak', 340,(255, 215, 0)),
        ('Flip Knife Lore', 'Field-Tested', 'StatTrak', 273,(255, 215, 0)),
        ('Flip Knife Lore', 'Well-Worn', 'StatTrak', 298,(255, 215, 0)),
        ('Flip Knife Lore', 'Battle-Scarred', 'StatTrak', 263,(255, 215, 0)),

        ('Huntsman Knife Marble Fade', 'Factory New', 'No', 318,(255, 215, 0)),
        ('Huntsman Knife Marble Fade', 'Minimal Wear', 'No', 330,(255, 215, 0)),
        ('Huntsman Knife Marble Fade', 'Factory New', 'StatTrak', 354,(255, 215, 0)),
        ('Huntsman Knife Marble Fade', 'Minimal Wear', 'StatTrak', 714,(255, 215, 0)),

        ('Huntsman Knife Scorched', 'Factory New', 'No', 259,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Minimal Wear', 'No', 129,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Field-Tested', 'No', 121,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Well-Worn', 'No', 100,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Battle-Scarred', 'No', 101,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Minimal Wear', 'StatTrak', 153,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Field-Tested', 'StatTrak', 133,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Well-Worn', 'StatTrak', 143,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Battle-Scarred', 'StatTrak', 197,(255, 215, 0)),

        ('Karambit Tiger Tooth', 'Factory New', 'No', 1230,(255, 215, 0)),
        ('Karambit Tiger Tooth', 'Minimal Wear', 'No', 1193,(255, 215, 0)),
        ('Karambit Tiger Tooth', 'Factory New', 'StatTrak', 1161,(255, 215, 0)),
        ('Karambit Tiger Tooth', 'Minimal Wear', 'StatTrak', 1199,(255, 215, 0)),

        ('AWP Dragon Lore', 'Factory New', 'No', 11173,(235, 75, 75)),
        ('AWP Dragon Lore', 'Minimal Wear', 'No', 8632,(235, 75, 75)),
        ('AWP Dragon Lore', 'Field-Tested', 'No', 6071,(235, 75, 75)),
        ('AWP Dragon Lore', 'Well-Worn', 'No', 5213,(235, 75, 75)),
        ('AWP Dragon Lore', 'Battle-Scarred', 'No', 4273,(235, 75, 75)),

        ('AK-47 Gold Arabesque', 'Factory New', 'No', 2740,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Minimal Wear', 'No', 2303,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Field-Tested', 'No', 1888,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Well-Worn', 'No', 1611,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Battle-Scarred', 'No', 1424,(235, 75, 75)),

        ('M4A4 Howl', 'Factory New', 'No', 6131,(255, 215, 0)),
        ('M4A4 Howl', 'Minimal Wear', 'No', 4606,(255, 215, 0)),
        ('M4A4 Howl', 'Field-Tested', 'No', 3958,(255, 215, 0)),
        ('M4A4 Howl', 'Well-Worn', 'No', 3768,(255, 215, 0)),
        ('M4A4 Howl', 'Factory New', 'StatTrak', 12400,(255, 215, 0)),
        ('M4A4 Howl', 'Minimal Wear', 'StatTrak', 8779,(255, 215, 0)),
        ('M4A4 Howl', 'Field-Tested', 'StatTrak', 6387,(255, 215, 0)),
        ('M4A4 Howl', 'Well-Worn', 'StatTrak', 7321,(255, 215, 0)),

        ('Butterfly Knife Gamma Doppler', 'Factory New', 'No', 3004,(255, 215, 0)),
        ('Butterfly Knife Gamma Doppler', 'Minimal Wear', 'No', 2827,(255, 215, 0)),
        ('Butterfly Knife Gamma Doppler', 'Factory New', 'StatTrak', 2822,(255, 215, 0)),
        ('Butterfly Knife Gamma Doppler', 'Minimal Wear', 'StatTrak', 2862,(255, 215, 0)),

        ('M9 Bayonet Gamma Doppler', 'Factory New', 'No', 1979,(255, 215, 0)),
        ('M9 Bayonet Gamma Doppler', 'Minimal Wear', 'No', 1838,(255, 215, 0)),
        ('M9 Bayonet Gamma Doppler', 'Factory New', 'StatTrak', 1797,(255, 215, 0)),
        ('M9 Bayonet Gamma Doppler', 'Minimal Wear', 'StatTrak', 1781,(255, 215, 0)),
    ]

    @staticmethod
    def get_skin_price(skin_name, condition, stattrak_status):
        for skin_data in SkinPriceRepository.SKIN_DATA:
            if (skin_data[0] == skin_name and 
                skin_data[1] == condition and 
                skin_data[2] == stattrak_status):
                return skin_data[3]
        return 0

    @staticmethod
    def get_skin_color(skin_name, condition, stattrak_status):
        for skin_data in SkinPriceRepository.SKIN_DATA:
            if (skin_data[0] == skin_name and 
                skin_data[1] == condition and 
                skin_data[2] == stattrak_status):
                return skin_data[4]
        return (75, 105, 255)

    @staticmethod
    def get_skins_files_names(min_price, max_price):
        if max_price < min_price:
            logger.warning(f"Invalid price range: max_price {max_price} < min_price {min_price}")
            return []

        skins_list = []
        unique_skins = set()
        
        for skin_data in SkinPriceRepository.SKIN_DATA:
            skin_name, condition, stattrak_status, price, color = skin_data
            if min_price <= price <= max_price:
                skin_file_name = f"{skin_name}.png"
                if skin_file_name not in unique_skins:
                    skins_list.append(skin_file_name)
                    unique_skins.add(skin_file_name)
        
        return skins_list

    @staticmethod
    def get_all_skins_with_prices():
        skins_data = {}
        
        for skin_data in SkinPriceRepository.SKIN_DATA:
            skin_name, condition, stattrak_status, price, color = skin_data
            
            if skin_name not in skins_data:
                skins_data[skin_name] = []
            
            skins_data[skin_name].append({
                'condition': condition,
                'stattrak_status': stattrak_status,
                'price': price,
                'color': color
            })
        
        return skins_data

class RaffleRollerAnimation:
    def __init__(self, width=700, height=200):
        self.width = width
        self.height = height
        self.roller_height = 200
        self.item_width = 180
        self.item_height = 150
        self.margin = 10
        
        self.bg_color = (0, 0, 0, 0)
        self.roller_bg = (0, 0, 0, 0)
        self.border_color = (60, 55, 89, 0)
        self.indicator_color = (209, 98, 102)
        self.item_bg = (20, 32, 43, 255)
        self.winning_border = (102, 178, 51)
        self.normal_border = (112, 103, 124)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.SKIN_FOLDER = os.path.join(current_dir, "skins")
        self.PREGENERATED_FOLDER = os.path.join(current_dir, "pregenerated_webp")
        
        Path(self.SKIN_FOLDER).mkdir(exist_ok=True)
        Path(self.PREGENERATED_FOLDER).mkdir(exist_ok=True)
        
        try:
            self.font_medium = ImageFont.truetype("arial.ttf", 22)
            self.font_small = ImageFont.truetype("arial.ttf", 18)
        except:
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def load_skin(self, skin_path, target_width, target_height):
        try:
            with Image.open(skin_path) as img:
                img = img.convert("RGBA")
                return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        except Exception as e:
            logger.error(f"Error loading skin {skin_path}: {e}")
            placeholder = Image.new('RGBA', (target_width, target_height), (100, 100, 100, 100))
            return placeholder

    def create_item(self, skin_img, stripe_color, is_winning=False):
        width, height = self.item_width, self.item_height
        
        item = Image.new('RGB', (width, height), self.item_bg[:3])
        draw = ImageDraw.Draw(item)
        
        blur_height = min(height // 3, 45)
        
        for y in range(blur_height):
            progress = y / blur_height
            r = int(self.item_bg[0] * (1 - progress) + stripe_color[0] * progress)
            g = int(self.item_bg[1] * (1 - progress) + stripe_color[1] * progress)
            b = int(self.item_bg[2] * (1 - progress) + stripe_color[2] * progress)
            draw.line([0, height - blur_height + y, width-1, height - blur_height + y], 
                    fill=(r, g, b))
        
        gradient_region = item.crop((0, height - blur_height, width, height))
        blurred_gradient = gradient_region.filter(ImageFilter.GaussianBlur(radius=3))
        item.paste(blurred_gradient, (0, height - blur_height))
        
        stripe_height = 10
        stripe_y = height - stripe_height
        draw.rectangle([0, stripe_y, width, height], fill=stripe_color)
        
        if skin_img:
            skin_x = (width - skin_img.width) // 2
            skin_y = (height - stripe_height - skin_img.height) // 2
            
            skin_rgba = skin_img.convert('RGBA')
            mask = skin_rgba.split()[3]
            item.paste(skin_rgba, (skin_x, skin_y), mask)
        
        return item

    def generate_roller_frame(self, skin_items, offset_x=0, winning_index=None):
        frame = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        
        start_x = 100 - offset_x
        for i, (skin_img, skin_name, price, condition, stattrak, stripe_color) in enumerate(skin_items):
            x_pos = start_x + i * (self.item_width + self.margin)
            
            if x_pos + self.item_width > 0 and x_pos < self.width:
                is_winning = (i == winning_index)
                item_img = self.create_item(skin_img, stripe_color, is_winning)
                
                item_rgba = item_img.convert('RGBA')
                mask = Image.new('L', (self.item_width, self.item_height), 255)
                frame.paste(item_rgba, (int(x_pos), (self.height - self.roller_height) // 2 + 20), mask)
        
        center_x = self.width // 2
        roller_y = (self.height - self.roller_height) // 2
        
        gold_colors = [
            (255, 215, 0),
            (255, 195, 0),
            (205, 173, 0),
        ]
        
        for i in range(6):
            color_idx = min(i // 2, len(gold_colors) - 1)
            alpha = 220 - (i * 20)
            gold_color = (*gold_colors[color_idx], alpha)
            draw.line([center_x + i, roller_y, center_x + i, roller_y + self.roller_height], 
                    fill=gold_color, width=1)
        
        draw.line([center_x, roller_y, center_x, roller_y + self.roller_height], 
                fill=(255, 255, 255, 180), width=1)
        draw.line([center_x + 5, roller_y, center_x + 5, roller_y + self.roller_height], 
                fill=(255, 255, 200, 160), width=1)
        
        if winning_index is not None and winning_index < len(skin_items):
            try:
                winning_skin_img, winning_skin_name, winning_price, winning_condition, winning_stattrak, winning_stripe_color = skin_items[winning_index]
                
                frame_color = winning_stripe_color
                
                info_width = 450
                info_height = 130
                
                info_x = (self.width - info_width) // 2
                info_y = 5
                
                info_bg = Image.new('RGBA', (info_width, info_height), (0, 0, 0, 0))
                info_draw = ImageDraw.Draw(info_bg)
                
                for y in range(info_height):
                    alpha = 240 - int(y / info_height * 40)
                    bg_color = (20, 25, 35, alpha)
                    info_draw.line([0, y, info_width, y], fill=bg_color)
                
                border_width = 4
                
                for i in range(border_width):
                    border_alpha = 255 - (i * 40)
                    border_color = (*frame_color, border_alpha)
                    info_draw.rectangle([i, i, info_width-1-i, info_height-1-i], 
                                    outline=border_color, width=1)
                
                info_draw.rectangle([border_width, border_width, info_width-1-border_width, info_height-1-border_width], 
                                outline=(255, 255, 255, 180), width=1)
                
                stattrak_text = "StatTrak™ " if winning_stattrak == "StatTrak" else ""
                name_text = f"{stattrak_text}{winning_skin_name}"
                name_bbox = info_draw.textbbox((0, 0), name_text, font=self.font_medium)
                name_width = name_bbox[2] - name_bbox[0]
                name_x = (info_width - name_width) // 2
                
                if winning_stattrak == "StatTrak":
                    name_color = (255, 215, 0)
                    name_shadow = (100, 80, 0)
                else:
                    name_color = (255, 255, 255)
                    name_shadow = (80, 80, 80)
                
                info_draw.text((name_x + 1, 25), name_text, fill=name_shadow, font=self.font_medium)
                info_draw.text((name_x, 24), name_text, fill=name_color, font=self.font_medium)
                
                condition_text = f"{winning_condition}"
                condition_bbox = info_draw.textbbox((0, 0), condition_text, font=self.font_small)
                condition_width = condition_bbox[2] - condition_bbox[0]
                condition_x = (info_width - condition_width) // 2
                
                condition_color = (220, 220, 220)
                condition_shadow = (80, 80, 80)
                
                info_draw.text((condition_x + 1, 58), condition_text, fill=condition_shadow, font=self.font_small)
                info_draw.text((condition_x, 57), condition_text, fill=condition_color, font=self.font_small)
                
                price_text = f"${winning_price}"
                price_bbox = info_draw.textbbox((0, 0), price_text, font=self.font_medium)
                price_width = price_bbox[2] - price_bbox[0]
                price_x = (info_width - price_width) // 2
                
                price_shadow_color = (100, 80, 0, 255)
                price_main_color = (255, 215, 0)
                price_highlight = (255, 235, 150)
                
                info_draw.text((price_x + 2, 88), price_text, fill=price_shadow_color, font=self.font_medium)
                info_draw.text((price_x, 86), price_text, fill=price_main_color, font=self.font_medium)
                info_draw.text((price_x + 1, 87), price_text, fill=price_highlight, font=self.font_medium)
                
                separator_y = 50
                line_color = (*frame_color, 180)
                info_draw.line([30, separator_y, info_width - 30, separator_y], 
                            fill=line_color, width=2)
                
                separator_y2 = 80
                info_draw.line([30, separator_y2, info_width - 30, separator_y2], 
                            fill=line_color, width=2)
                
                corner_size = 12
                corner_color = (*frame_color, 220)
                
                info_draw.line([0, 0, corner_size, 0], fill=corner_color, width=2)
                info_draw.line([0, 0, 0, corner_size], fill=corner_color, width=2)
                info_draw.line([info_width-1, 0, info_width-1-corner_size, 0], fill=corner_color, width=2)
                info_draw.line([info_width-1, 0, info_width-1, corner_size], fill=corner_color, width=2)
                info_draw.line([0, info_height-1, corner_size, info_height-1], fill=corner_color, width=2)
                info_draw.line([0, info_height-1, 0, info_height-1-corner_size], fill=corner_color, width=2)
                info_draw.line([info_width-1, info_height-1, info_width-1-corner_size, info_height-1], fill=corner_color, width=2)
                info_draw.line([info_width-1, info_height-1, info_width-1, info_height-1-corner_size], fill=corner_color, width=2)
                
                frame.paste(info_bg, (info_x, info_y), info_bg)
                
            except Exception as e:
                logger.error(f"End label error: {e}")

        return frame

    def create_animation_optimized(self, target_combination, output_path, min_price, max_price):
        try:
            import math
            
            all_skins_data = SkinPriceRepository.get_all_skins_with_prices()
            skin_items = []
            
            selected_skins = []
            for skin_name, price_infos in all_skins_data.items():
                for price_info in price_infos:
                    if min_price <= price_info['price'] <= max_price:
                        selected_skins.append({
                            'name': skin_name,
                            'condition': price_info['condition'],
                            'stattrak': price_info['stattrak_status'],
                            'price': price_info['price'],
                            'color': price_info['color']
                        })
            
            random.shuffle(selected_skins)
            
            extended_skins = []
            while len(extended_skins) < 140:
                chunk = selected_skins.copy()
                random.shuffle(chunk)
                extended_skins.extend(chunk)
            selected_skins = extended_skins[:140]
            
            random.shuffle(selected_skins)
            
            WINNING_POSITION = 40
            
            ITEM_WIDTH = (self.item_width + self.margin)
            random_offset = random.uniform(10, ITEM_WIDTH)
            
            for i, skin_data in enumerate(selected_skins):
                skin_path = Path(self.SKIN_FOLDER) / f"{skin_data['name']}.png"
                skin_img = None
                if skin_path.exists():
                    skin_img = self.load_skin(skin_path, 140, 110)
                
                if i == WINNING_POSITION:
                    target_skin_path = Path(self.SKIN_FOLDER) / f"{target_combination.skin_name}.png"
                    target_skin_img = None
                    if target_skin_path.exists():
                        target_skin_img = self.load_skin(target_skin_path, 140, 110)
                    
                    target_color = SkinPriceRepository.get_skin_color(
                        target_combination.skin_name,
                        target_combination.condition,
                        target_combination.stattrak_status
                    )
                    
                    skin_items.append((
                        target_skin_img,
                        target_combination.skin_name,
                        target_combination.price,
                        target_combination.condition,
                        target_combination.stattrak_status,
                        target_color
                    ))
                else:
                    skin_items.append((
                        skin_img,
                        skin_data['name'],
                        skin_data['price'],
                        skin_data['condition'],
                        skin_data['stattrak'],
                        skin_data['color']
                    ))
            
            frames = []
            
            base_distance = WINNING_POSITION * (self.item_width + self.margin) - self.width // 2 + self.item_width // 2
            total_distance = base_distance + random_offset
            num_roll_frames = 100
            
            for i in range(num_roll_frames):
                if i < 20:
                    continue
                    
                progress = i / num_roll_frames
                
                if progress < 0.02:
                    phase_progress = progress / 0.02
                    eased_progress = phase_progress * phase_progress * phase_progress
                else:
                    phase_progress = (progress - 0.02) / 0.98
                    eased_progress = 1 - math.pow(1 - phase_progress, 3)
                    eased_progress = 0.02 + (eased_progress * 0.98)
                
                current_offset = total_distance * eased_progress
                frames.append(self.generate_roller_frame(skin_items, current_offset))
            
            for i in range(5):
                frames.append(self.generate_roller_frame(skin_items, total_distance))
            
            for i in range(30):
                frames.append(self.generate_roller_frame(skin_items, total_distance, WINNING_POSITION))
            
            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=50,
                    loop=0,
                    format='WEBP',
                    quality=85,
                    method=4,
                    save_transparent=True
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return False

class CaseOpeningAnimationGenerator:
    def __init__(self):
        self.MIN_PRICE = 0
        self.MAX_PRICE = 60
        self.PRICE_RANGE = (self.MIN_PRICE, self.MAX_PRICE)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.SKIN_FOLDER = os.path.join(current_dir, "skins")
        self.PREGENERATED_FOLDER = os.path.join(current_dir, "pregenerated_webp")
        
        self.webp_supported = self.check_webp_support()
        logger.info(f"WEBP support: {self.webp_supported}")
        
        Path(self.SKIN_FOLDER).mkdir(exist_ok=True)
        Path(self.PREGENERATED_FOLDER).mkdir(exist_ok=True)

    def check_webp_support(self):
        try:
            test_image = Image.new('RGB', (10, 10), 'red')
            test_image.save('test.webp', 'WEBP')
            
            with Image.open('test.webp') as img:
                pass
                
            if os.path.exists('test.webp'):
                os.remove('test.webp')
                
            return True
        except Exception as e:
            logger.warning(f"WEBP not supported: {e}")
            return False

    class SkinCombination:
        def __init__(self, skin_name, condition, stattrak_status, price):
            self.skin_name = skin_name
            self.condition = condition
            self.stattrak_status = stattrak_status
            self.price = price
            
        def __str__(self):
            stattrak_text = "StatTrak™ " if self.stattrak_status == "StatTrak" else ""
            return f"{stattrak_text}{self.skin_name} {self.condition} (${self.price})"

    def get_all_skin_combinations_in_range(self, min_price, max_price):
        combinations = []
        
        try:
            all_skins_data = SkinPriceRepository.get_all_skins_with_prices()
            
            for skin_name, price_infos in all_skins_data.items():
                for price_info in price_infos:
                    price = price_info['price']
                    condition = price_info['condition']
                    stattrak_status = price_info['stattrak_status']
                    
                    if min_price <= price <= max_price:
                        possible_filenames = [
                            f"{skin_name}.png",
                            f"{skin_name.lower()}.png",
                            f"{skin_name.upper()}.png",
                        ]
                        
                        skin_found = False
                        for filename in possible_filenames:
                            skin_path = Path(self.SKIN_FOLDER) / filename
                            if skin_path.exists():
                                combinations.append(
                                    self.SkinCombination(skin_name, condition, stattrak_status, price)
                                )
                                skin_found = True
                                break
        
            logger.info(f"Found {len(combinations)} valid skin combinations in range ${min_price}-${max_price}")
            return combinations
            
        except Exception as e:
            logger.error(f"Error getting skin combinations: {e}")
            return []

    def generate_filename(self, combination, animation_number):
        return f"case_10_{animation_number}_({combination.price})_2.webp"

    def pregenerate_single_animation_optimized(self, combination, animation_number, min_price, max_price):
        try:
            filename = self.generate_filename(combination, animation_number)
            output_path = Path(self.PREGENERATED_FOLDER) / filename
            
            if output_path.exists():
                logger.info(f"Animation already exists: {filename}")
                return True, None
                
            raffle_animator = RaffleRollerAnimation()
            success = raffle_animator.create_animation_optimized(
                combination, 
                str(output_path),
                min_price,
                max_price
            )
            
            if success:
                file_size = os.path.getsize(output_path) / 1024
                logger.info(f"Animation created: {filename} ({file_size:.1f} KB)")
                return True, None
            else:
                return False, "Animation creation failed"
                
        except Exception as e:
            logger.error(f"Error in pregeneration: {e}")
            return False, str(e)

    def pregenerate_all_animations_optimized(self, min_price=None, max_price=None):
        if min_price is None:
            min_price = self.MIN_PRICE
        if max_price is None:
            max_price = self.MAX_PRICE
            
        self.PRICE_RANGE = (min_price, max_price)
        
        logger.info(f"Starting pregeneration for price range ${min_price}-${max_price}")
        
        start_time = time.time()
        
        try:
            combinations = self.get_all_skin_combinations_in_range(min_price, max_price)
            logger.info(f"Found {len(combinations)} valid skin combinations")
            
            if not combinations:
                logger.error("No skin combinations found!")
                return 0, 0
                
            success_count = 0
            error_count = 0
            total = len(combinations)
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_to_combination = {}
                animation_counter = 1
                
                for combo in combinations:
                    future = executor.submit(
                        self.pregenerate_single_animation_optimized, 
                        combo, 
                        animation_counter,
                        min_price,
                        max_price
                    )
                    future_to_combination[future] = (combo, animation_counter)
                    animation_counter += 1
                
                for i, future in enumerate(as_completed(future_to_combination), 1):
                    combination, anim_num = future_to_combination[future]
                    
                    try:
                        success, error_message = future.result()
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                            logger.error(f"Error for {combination}: {error_message}")
                        
                        if i % 10 == 0 or i == total:
                            progress = (i / total) * 100
                            logger.info(f"Progress: {i}/{total} ({progress:.1f}%) - Success: {success_count}, Errors: {error_count}")
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Exception for {combination}: {e}")
        
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Success: {success_count}")
            logger.info(f"Errors: {error_count}")
            logger.info(f"Total time: {duration:.2f} seconds")
            
            return total, sum(combo.price for combo in combinations)
            
        except Exception as e:
            logger.error(f"Error during pregeneration: {e}")
            return 0, 0

def main():
    generator = CaseOpeningAnimationGenerator()
    
    min_price = generator.MIN_PRICE
    max_price = generator.MAX_PRICE
    
    combinations = generator.get_all_skin_combinations_in_range(min_price, max_price)
    
    generator.pregenerate_all_animations_optimized(min_price, max_price)
    
    total_price = sum(combo.price for combo in combinations)
    total_animations = len(combinations)
    
    print(f"Price range: ${min_price}-${max_price}")
    print(f"Price sum: ${total_price}")
    print(f"Files count: {total_animations}")

if __name__ == "__main__":
    main()