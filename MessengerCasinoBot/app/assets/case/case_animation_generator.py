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

        ('AK-47 Wasteland Rebel', 'Factory New', 'No', 467, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Minimal Wear', 'No', 153, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Field-Tested', 'No', 80, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Well-Worn', 'No', 80, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Battle-Scarred', 'No', 80, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Factory New', 'StatTrak', 1554, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Minimal Wear', 'StatTrak', 176, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Field-Tested', 'StatTrak', 114, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Well-Worn', 'StatTrak', 133, (235, 75, 75)),
        ('AK-47 Wasteland Rebel', 'Battle-Scarred', 'StatTrak', 119, (235, 75, 75)),

        ('AWP Asiimov', 'Field-Tested', 'No', 124, (235, 75, 75)),
        ('AWP Asiimov', 'Well-Worn', 'No', 94, (235, 75, 75)),
        ('AWP Asiimov', 'Battle-Scarred', 'No', 78, (235, 75, 75)),
        ('AWP Asiimov', 'Field-Tested', 'StatTrak', 241, (235, 75, 75)),
        ('AWP Asiimov', 'Well-Worn', 'StatTrak', 185, (235, 75, 75)),
        ('AWP Asiimov', 'Battle-Scarred', 'StatTrak', 142, (235, 75, 75)),

        ('AUG Chameleon', 'Factory New', 'No', 90, (235, 75, 75)),
        ('AUG Chameleon', 'Minimal Wear', 'No', 78, (235, 75, 75)),
        ('AUG Chameleon', 'Field-Tested', 'No', 75, (235, 75, 75)),
        ('AUG Chameleon', 'Well-Worn', 'No', 73, (235, 75, 75)),
        ('AUG Chameleon', 'Battle-Scarred', 'No', 74, (235, 75, 75)),
        ('AUG Chameleon', 'Factory New', 'StatTrak', 97, (235, 75, 75)),
        ('AUG Chameleon', 'Minimal Wear', 'StatTrak', 72, (235, 75, 75)),
        ('AUG Chameleon', 'Field-Tested', 'StatTrak', 67, (235, 75, 75)),
        ('AUG Chameleon', 'Well-Worn', 'StatTrak', 88, (235, 75, 75)),
        ('AUG Chameleon', 'Battle-Scarred', 'StatTrak', 72, (235, 75, 75)),

        ('AK-47 Redline', 'Minimal Wear', 'No', 197, (211, 44, 230)),
        ('AK-47 Redline', 'Field-Tested', 'No', 33, (211, 44, 230)),
        ('AK-47 Redline', 'Well-Worn', 'No', 29, (211, 44, 230)),
        ('AK-47 Redline', 'Battle-Scarred', 'No', 28, (211, 44, 230)),
        ('AK-47 Redline', 'Minimal Wear', 'StatTrak', 348, (211, 44, 230)),
        ('AK-47 Redline', 'Field-Tested', 'StatTrak', 71, (211, 44, 230)),
        ('AK-47 Redline', 'Well-Worn', 'StatTrak', 56, (211, 44, 230)),
        ('AK-47 Redline', 'Battle-Scarred', 'StatTrak', 54, (211, 44, 230)),

        ('SG 553 Pulse', 'Minimal Wear', 'No', 8, (136, 71, 255)),
        ('SG 553 Pulse', 'Field-Tested', 'No', 3, (136, 71, 255)),
        ('SG 553 Pulse', 'Well-Worn', 'No', 3, (136, 71, 255)),
        ('SG 553 Pulse', 'Battle-Scarred', 'No', 2, (136, 71, 255)),
        ('SG 553 Pulse', 'Minimal Wear', 'StatTrak', 12, (136, 71, 255)),
        ('SG 553 Pulse', 'Field-Tested', 'StatTrak', 5, (136, 71, 255)),
        ('SG 553 Pulse', 'Well-Worn', 'StatTrak', 4, (136, 71, 255)),
        ('SG 553 Pulse', 'Battle-Scarred', 'StatTrak', 4, (136, 71, 255)),

        ('USP-S Guardian', 'Factory New', 'No', 8, (136, 71, 255)),
        ('USP-S Guardian', 'Minimal Wear', 'No', 4, (136, 71, 255)),
        ('USP-S Guardian', 'Field-Tested', 'No', 3, (136, 71, 255)),
        ('USP-S Guardian', 'Factory New', 'StatTrak', 13, (136, 71, 255)),
        ('USP-S Guardian', 'Minimal Wear', 'StatTrak', 8, (136, 71, 255)),
        ('USP-S Guardian', 'Field-Tested', 'StatTrak', 7, (136, 71, 255)),

        ('MAG-7 Heaven Guard', 'Factory New', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Minimal Wear', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Field-Tested', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Well-Worn', 'No', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Factory New', 'StatTrak', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Minimal Wear', 'StatTrak', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Field-Tested', 'StatTrak', 1, (75, 105, 255)),
        ('MAG-7 Heaven Guard', 'Well-Worn', 'StatTrak', 2, (75, 105, 255)),

        ('M4A4 Griffin', 'Factory New', 'No', 80, (136, 71, 255)),
        ('M4A4 Griffin', 'Minimal Wear', 'No', 6, (136, 71, 255)),
        ('M4A4 Griffin', 'Field-Tested', 'No', 3, (136, 71, 255)),
        ('M4A4 Griffin', 'Well-Worn', 'No', 5, (136, 71, 255)),
        ('M4A4 Griffin', 'Battle-Scarred', 'No', 4, (136, 71, 255)),
        ('M4A4 Griffin', 'Factory New', 'StatTrak', 26, (136, 71, 255)),
        ('M4A4 Griffin', 'Minimal Wear', 'StatTrak', 10, (136, 71, 255)),
        ('M4A4 Griffin', 'Field-Tested', 'StatTrak', 8, (136, 71, 255)),
        ('M4A4 Griffin', 'Well-Worn', 'StatTrak', 11, (136, 71, 255)),
        ('M4A4 Griffin', 'Battle-Scarred', 'StatTrak', 10, (136, 71, 255)),

        ('Tec-9 Sandstorm', 'Minimal Wear', 'No', 2, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Field-Tested', 'No', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Well-Worn', 'No', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Battle-Scarred', 'No', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Minimal Wear', 'StatTrak', 4, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Field-Tested', 'StatTrak', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Well-Worn', 'StatTrak', 1, (75, 105, 255)),
        ('Tec-9 Sandstorm', 'Battle-Scarred', 'StatTrak', 1, (75, 105, 255)),

        ('P2000 Fire Elemental', 'Factory New', 'No', 180, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Minimal Wear', 'No', 82, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Field-Tested', 'No', 78, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Well-Worn', 'No', 82, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Battle-Scarred', 'No', 77, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Factory New', 'StatTrak', 179, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Minimal Wear', 'StatTrak', 93, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Field-Tested', 'StatTrak', 76, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Well-Worn', 'StatTrak', 87, (235, 75, 75)),
        ('P2000 Fire Elemental', 'Battle-Scarred', 'StatTrak', 86, (235, 75, 75)),

        ('M4A1-S Cyrex', 'Factory New', 'No', 212,  (235, 75, 75)),
        ('M4A1-S Cyrex', 'Minimal Wear', 'No', 182, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Field-Tested', 'No', 175, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Well-Worn', 'No', 169, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Battle-Scarred', 'No', 170, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Factory New', 'StatTrak', 232, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Minimal Wear', 'StatTrak', 183, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Field-Tested', 'StatTrak', 160, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Well-Worn', 'StatTrak', 165, (235, 75, 75)),
        ('M4A1-S Cyrex', 'Battle-Scarred', 'StatTrak', 173, (235, 75, 75)),

        ('P90 Asiimov', 'Factory New', 'No', 247, (235, 75, 75)),
        ('P90 Asiimov', 'Minimal Wear', 'No', 190, (235, 75, 75)),
        ('P90 Asiimov', 'Field-Tested', 'No', 181, (235, 75, 75)),
        ('P90 Asiimov', 'Well-Worn', 'No', 165, (235, 75, 75)),
        ('P90 Asiimov', 'Battle-Scarred', 'No', 162, (235, 75, 75)),
        ('P90 Asiimov', 'Factory New', 'StatTrak', 256, (235, 75, 75)),
        ('P90 Asiimov', 'Minimal Wear', 'StatTrak', 188, (235, 75, 75)),
        ('P90 Asiimov', 'Field-Tested', 'StatTrak', 164, (235, 75, 75)),
        ('P90 Asiimov', 'Well-Worn', 'StatTrak', 162, (235, 75, 75)),
        ('P90 Asiimov', 'Battle-Scarred', 'StatTrak', 164, (235, 75, 75)),

        ('Glock-18 Water Elemental', 'Factory New', 'No', 35, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Minimal Wear', 'No', 19, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Field-Tested', 'No', 18, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Well-Worn', 'No', 18, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Battle-Scarred', 'No', 18, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Factory New', 'StatTrak', 63, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Minimal Wear', 'StatTrak', 35, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Field-Tested', 'StatTrak', 21, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Well-Worn', 'StatTrak', 29, (211, 44, 230)),
        ('Glock-18 Water Elemental', 'Battle-Scarred', 'StatTrak', 24, (211, 44, 230)),

        ('CZ75-Auto Tigris', 'Factory New', 'No', 7, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Minimal Wear', 'No', 2, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Field-Tested', 'No', 2, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Well-Worn', 'No', 2, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Battle-Scarred', 'No', 1, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Factory New', 'StatTrak', 8, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Minimal Wear', 'StatTrak', 3, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Field-Tested', 'StatTrak', 2, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Well-Worn', 'StatTrak', 2, (136, 71, 255)),
        ('CZ75-Auto Tigris', 'Battle-Scarred', 'StatTrak', 2, (136, 71, 255)),

        ('PP-Bizon Osiris', 'Factory New', 'No', 3, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Minimal Wear', 'No', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Field-Tested', 'No', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Well-Worn', 'No', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Battle-Scarred', 'No', 1, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Factory New', 'StatTrak', 5, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Minimal Wear', 'StatTrak', 3, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Field-Tested', 'StatTrak', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Well-Worn', 'StatTrak', 2, (136, 71, 255)),
        ('PP-Bizon Osiris', 'Battle-Scarred', 'StatTrak', 2, (136, 71, 255)),

        ('Nova Koi', 'Factory New', 'No', 3, (136, 71, 255)),
        ('Nova Koi', 'Minimal Wear', 'No', 2, (136, 71, 255)),
        ('Nova Koi', 'Field-Tested', 'No', 2, (136, 71, 255)),
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

        ('SSG 08 Abyss', 'Factory New', 'No', 5, (75, 105, 255)),
        ('SSG 08 Abyss', 'Minimal Wear', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Field-Tested', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Well-Worn', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Battle-Scarred', 'No', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Factory New', 'StatTrak', 13, (75, 105, 255)),
        ('SSG 08 Abyss', 'Minimal Wear', 'StatTrak', 2, (75, 105, 255)),
        ('SSG 08 Abyss', 'Field-Tested', 'StatTrak', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Well-Worn', 'StatTrak', 1, (75, 105, 255)),
        ('SSG 08 Abyss', 'Battle-Scarred', 'StatTrak', 1, (75, 105, 255)),

        ('M4A1-S Bright Water', 'Minimal Wear', 'No', 74, (136, 71, 255)),
        ('M4A1-S Bright Water', 'Field-Tested', 'No', 38, (136, 71, 255)),
        ('M4A1-S Bright Water', 'Minimal Wear', 'StatTrak', 71, (136, 71, 255)),
        ('M4A1-S Bright Water', 'Field-Tested', 'StatTrak', 66, (136, 71, 255)),

        ('AK-47 Fire Serpent', 'Factory New', 'No', 2900,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Minimal Wear', 'No', 1400,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Field-Tested', 'No', 850,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Well-Worn', 'No', 828,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Battle-Scarred', 'No', 555,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Factory New', 'StatTrak', 4902,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Minimal Wear', 'StatTrak', 2952,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Field-Tested', 'StatTrak', 1703,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Well-Worn', 'StatTrak', 1439,(235, 75, 75)),
        ('AK-47 Fire Serpent', 'Battle-Scarred', 'StatTrak', 1442,(235, 75, 75)),

        ('AK-47 Vulcan', 'Factory New', 'No', 752,(235, 75, 75)),
        ('AK-47 Vulcan', 'Minimal Wear', 'No', 421,(235, 75, 75)),
        ('AK-47 Vulcan', 'Field-Tested', 'No', 213,(235, 75, 75)),
        ('AK-47 Vulcan', 'Well-Worn', 'No', 146,(235, 75, 75)),
        ('AK-47 Vulcan', 'Battle-Scarred', 'No', 125,(235, 75, 75)),
        ('AK-47 Vulcan', 'Factory New', 'StatTrak', 1481,(235, 75, 75)),
        ('AK-47 Vulcan', 'Minimal Wear', 'StatTrak', 862,(235, 75, 75)),
        ('AK-47 Vulcan', 'Field-Tested', 'StatTrak', 374,(235, 75, 75)),
        ('AK-47 Vulcan', 'Well-Worn', 'StatTrak', 260,(235, 75, 75)),
        ('AK-47 Vulcan', 'Battle-Scarred', 'StatTrak', 223,(235, 75, 75)),

        ('AUG Torque', 'Factory New', 'No', 13,(136, 71, 255)),
        ('AUG Torque', 'Minimal Wear', 'No', 10,(136, 71, 255)),
        ('AUG Torque', 'Field-Tested', 'No', 6,(136, 71, 255)),
        ('AUG Torque', 'Well-Worn', 'No', 6,(136, 71, 255)),
        ('AUG Torque', 'Battle-Scarred', 'No', 5,(136, 71, 255)),
        ('AUG Torque', 'Factory New', 'StatTrak', 12,(136, 71, 255)),
        ('AUG Torque', 'Minimal Wear', 'StatTrak', 9,(136, 71, 255)),
        ('AUG Torque', 'Field-Tested', 'StatTrak', 7,(136, 71, 255)),
        ('AUG Torque', 'Well-Worn', 'StatTrak', 8,(136, 71, 255)),
        ('AUG Torque', 'Battle-Scarred', 'StatTrak', 9,(136, 71, 255)),

        ('Tec-9 Isaac', 'Factory New', 'No', 21,(75, 105, 255)),
        ('Tec-9 Isaac', 'Minimal Wear', 'No', 5,(75, 105, 255)),
        ('Tec-9 Isaac', 'Field-Tested', 'No', 3,(75, 105, 255)),
        ('Tec-9 Isaac', 'Well-Worn', 'No', 2,(75, 105, 255)),
        ('Tec-9 Isaac', 'Battle-Scarred', 'No', 2,(75, 105, 255)),
        ('Tec-9 Isaac', 'Factory New', 'StatTrak', 35,(75, 105, 255)),
        ('Tec-9 Isaac', 'Minimal Wear', 'StatTrak', 8,(75, 105, 255)),
        ('Tec-9 Isaac', 'Field-Tested', 'StatTrak', 4,(75, 105, 255)),
        ('Tec-9 Isaac', 'Well-Worn', 'StatTrak', 3,(75, 105, 255)),
        ('Tec-9 Isaac', 'Battle-Scarred', 'StatTrak', 3,(75, 105, 255)),

        ('P90 Module', 'Factory New', 'No', 2,(75, 105, 255)),
        ('P90 Module', 'Minimal Wear', 'No', 2,(75, 105, 255)),
        ('P90 Module', 'Field-Tested', 'No', 2,(75, 105, 255)),
        ('P90 Module', 'Factory New', 'StatTrak', 3,(75, 105, 255)),
        ('P90 Module', 'Minimal Wear', 'StatTrak', 2,(75, 105, 255)),
        ('P90 Module', 'Field-Tested', 'StatTrak', 2,(75, 105, 255)),

        ('P2000 Pulse', 'Factory New', 'No', 3,(75, 105, 255)),
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

        ('AK-47 Aquamarine Revenge', 'Factory New', 'No', 289,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Minimal Wear', 'No', 77,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Field-Tested', 'No', 44,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Well-Worn', 'No', 40,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Battle-Scarred', 'No', 39,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Factory New', 'StatTrak', 334,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Minimal Wear', 'StatTrak', 173,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Field-Tested', 'StatTrak', 92,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Well-Worn', 'StatTrak', 66,(235, 75, 75)),
        ('AK-47 Aquamarine Revenge', 'Battle-Scarred', 'StatTrak', 68,(235, 75, 75)),

        ('AWP Hyper Beast', 'Factory New', 'No', 240,(235, 75, 75)),
        ('AWP Hyper Beast', 'Minimal Wear', 'No', 58,(235, 75, 75)),
        ('AWP Hyper Beast', 'Field-Tested', 'No', 37,(235, 75, 75)),
        ('AWP Hyper Beast', 'Well-Worn', 'No', 34,(235, 75, 75)),
        ('AWP Hyper Beast', 'Battle-Scarred', 'No', 34,(235, 75, 75)),
        ('AWP Hyper Beast', 'Factory New', 'StatTrak', 264,(235, 75, 75)),
        ('AWP Hyper Beast', 'Minimal Wear', 'StatTrak', 130,(235, 75, 75)),
        ('AWP Hyper Beast', 'Field-Tested', 'StatTrak', 69,(235, 75, 75)),
        ('AWP Hyper Beast', 'Well-Worn', 'StatTrak', 63,(235, 75, 75)),
        ('AWP Hyper Beast', 'Battle-Scarred', 'StatTrak', 66,(235, 75, 75)),

        ('M4A4 Evil Daimyo', 'Factory New', 'No', 10,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Minimal Wear', 'No', 4,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Field-Tested', 'No', 3,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Well-Worn', 'No', 3,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Battle-Scarred', 'No', 3,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Factory New', 'StatTrak', 20,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Minimal Wear', 'StatTrak', 11,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Field-Tested', 'StatTrak', 8,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Well-Worn', 'StatTrak', 8,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Battle-Scarred', 'StatTrak', 8,(136, 71, 255)),

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

        ('Karambit Safari Mesh', 'Factory New', 'No', 760,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Minimal Wear', 'No', 400,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Field-Tested', 'No', 383,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Well-Worn', 'No', 399,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Battle-Scarred', 'No', 386,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Minimal Wear', 'StatTrak', 490,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Field-Tested', 'StatTrak', 388,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Well-Worn', 'StatTrak', 440,(255, 215, 0)),
        ('Karambit Safari Mesh', 'Battle-Scarred', 'StatTrak', 394,(255, 215, 0)),

        ('Butterfly Knife Fade', 'Factory New', 'No', 2663,(255, 215, 0)),
        ('Butterfly Knife Fade', 'Minimal Wear', 'No', 2557,(255, 215, 0)),
        ('Butterfly Knife Fade', 'Factory New', 'StatTrak', 2473,(255, 215, 0)),
        ('Butterfly Knife Fade', 'Minimal Wear', 'StatTrak', 2548,(255, 215, 0)),

        ('Butterfly Knife Ultraviolet', 'Factory New', 'No', 1965,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Minimal Wear', 'No', 847,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Field-Tested', 'No', 622,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Well-Worn', 'No', 588,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Battle-Scarred', 'No', 520,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Factory New', 'StatTrak', 2756,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Minimal Wear', 'StatTrak', 890,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Field-Tested', 'StatTrak', 647,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Well-Worn', 'StatTrak', 582,(255, 215, 0)),
        ('Butterfly Knife Ultraviolet', 'Battle-Scarred', 'StatTrak', 525,(255, 215, 0)),

        ('Bayonet Slaughter', 'Factory New', 'No', 400,(255, 215, 0)),
        ('Bayonet Slaughter', 'Minimal Wear', 'No', 313,(255, 215, 0)),
        ('Bayonet Slaughter', 'Field-Tested', 'No', 289,(255, 215, 0)),
        ('Bayonet Slaughter', 'Factory New', 'StatTrak', 478,(255, 215, 0)),
        ('Bayonet Slaughter', 'Minimal Wear', 'StatTrak', 450,(255, 215, 0)),
        ('Bayonet Slaughter', 'Field-Tested', 'StatTrak', 393,(255, 215, 0)),

        ('Bayonet Urban Masked', 'Factory New', 'No', 380,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Minimal Wear', 'No', 161,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Field-Tested', 'No', 130,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Well-Worn', 'No', 129,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Battle-Scarred', 'No', 925,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Minimal Wear', 'StatTrak', 237,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Field-Tested', 'StatTrak', 148,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Well-Worn', 'StatTrak', 203,(255, 215, 0)),
        ('Bayonet Urban Masked', 'Battle-Scarred', 'StatTrak', 166,(255, 215, 0)),

        ('Falchion Knife Case Hardened', 'Factory New', 'No', 319,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Minimal Wear', 'No', 178,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Field-Tested', 'No', 163,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Well-Worn', 'No', 147,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Battle-Scarred', 'No', 145,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Factory New', 'StatTrak', 449,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Minimal Wear', 'StatTrak', 304,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Field-Tested', 'StatTrak', 224,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Well-Worn', 'StatTrak', 227,(255, 215, 0)),
        ('Falchion Knife Case Hardened', 'Battle-Scarred', 'StatTrak', 210,(255, 215, 0)),

        ('Gut Knife Freehand', 'Factory New', 'No', 82,(255, 215, 0)),
        ('Gut Knife Freehand', 'Minimal Wear', 'No', 67,(255, 215, 0)),
        ('Gut Knife Freehand', 'Field-Tested', 'No', 66,(255, 215, 0)),
        ('Gut Knife Freehand', 'Well-Worn', 'No', 84,(255, 215, 0)),
        ('Gut Knife Freehand', 'Battle-Scarred', 'No', 71,(255, 215, 0)),
        ('Gut Knife Freehand', 'Factory New', 'StatTrak', 110,(255, 215, 0)),
        ('Gut Knife Freehand', 'Minimal Wear', 'StatTrak', 79,(255, 215, 0)),
        ('Gut Knife Freehand', 'Field-Tested', 'StatTrak', 79,(255, 215, 0)),
        ('Gut Knife Freehand', 'Well-Worn', 'StatTrak', 95,(255, 215, 0)),
        ('Gut Knife Freehand', 'Battle-Scarred', 'StatTrak', 144,(255, 215, 0)),

        ('Flip Knife Lore', 'Factory New', 'No', 285,(255, 215, 0)),
        ('Flip Knife Lore', 'Minimal Wear', 'No', 207,(255, 215, 0)),
        ('Flip Knife Lore', 'Field-Tested', 'No', 164,(255, 215, 0)),
        ('Flip Knife Lore', 'Well-Worn', 'No', 167,(255, 215, 0)),
        ('Flip Knife Lore', 'Battle-Scarred', 'No', 156,(255, 215, 0)),
        ('Flip Knife Lore', 'Factory New', 'StatTrak', 368,(255, 215, 0)),
        ('Flip Knife Lore', 'Minimal Wear', 'StatTrak', 235,(255, 215, 0)),
        ('Flip Knife Lore', 'Field-Tested', 'StatTrak', 191,(255, 215, 0)),
        ('Flip Knife Lore', 'Well-Worn', 'StatTrak', 274,(255, 215, 0)),
        ('Flip Knife Lore', 'Battle-Scarred', 'StatTrak', 205,(255, 215, 0)),

        ('Huntsman Knife Marble Fade', 'Factory New', 'No', 195,(255, 215, 0)),
        ('Huntsman Knife Marble Fade', 'Minimal Wear', 'No', 265,(255, 215, 0)),
        ('Huntsman Knife Marble Fade', 'Factory New', 'StatTrak', 252,(255, 215, 0)),
        ('Huntsman Knife Marble Fade', 'Minimal Wear', 'StatTrak', 450,(255, 215, 0)),

        ('Huntsman Knife Scorched', 'Factory New', 'No', 325,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Minimal Wear', 'No', 91,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Field-Tested', 'No', 68,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Well-Worn', 'No', 74,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Battle-Scarred', 'No', 72,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Minimal Wear', 'StatTrak', 149,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Field-Tested', 'StatTrak', 102,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Well-Worn', 'StatTrak', 133,(255, 215, 0)),
        ('Huntsman Knife Scorched', 'Battle-Scarred', 'StatTrak', 116,(255, 215, 0)),

        ('Karambit Tiger Tooth', 'Factory New', 'No', 982,(255, 215, 0)),
        ('Karambit Tiger Tooth', 'Minimal Wear', 'No', 959,(255, 215, 0)),
        ('Karambit Tiger Tooth', 'Factory New', 'StatTrak', 975,(255, 215, 0)),
        ('Karambit Tiger Tooth', 'Minimal Wear', 'StatTrak', 1250,(255, 215, 0)),

        ('AWP Dragon Lore', 'Factory New', 'No', 12007,(235, 75, 75)),
        ('AWP Dragon Lore', 'Minimal Wear', 'No', 9229,(235, 75, 75)),
        ('AWP Dragon Lore', 'Field-Tested', 'No', 6600,(235, 75, 75)),
        ('AWP Dragon Lore', 'Well-Worn', 'No', 5889,(235, 75, 75)),
        ('AWP Dragon Lore', 'Battle-Scarred', 'No', 4900,(235, 75, 75)),

        ('AK-47 Gold Arabesque', 'Factory New', 'No', 4070,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Minimal Wear', 'No', 2739,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Field-Tested', 'No', 1953,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Well-Worn', 'No', 1703,(235, 75, 75)),
        ('AK-47 Gold Arabesque', 'Battle-Scarred', 'No', 1425,(235, 75, 75)),

        ('M4A4 Howl', 'Factory New', 'No', 7070,(255, 215, 0)),
        ('M4A4 Howl', 'Minimal Wear', 'No', 5224,(255, 215, 0)),
        ('M4A4 Howl', 'Field-Tested', 'No', 4422,(255, 215, 0)),
        ('M4A4 Howl', 'Well-Worn', 'No', 4123,(255, 215, 0)),
        ('M4A4 Howl', 'Factory New', 'StatTrak', 15149,(255, 215, 0)),
        ('M4A4 Howl', 'Minimal Wear', 'StatTrak', 9494,(255, 215, 0)),
        ('M4A4 Howl', 'Field-Tested', 'StatTrak', 7854,(255, 215, 0)),
        ('M4A4 Howl', 'Well-Worn', 'StatTrak', 7237,(255, 215, 0)),

        ('Butterfly Knife Gamma Doppler', 'Factory New', 'No', 2249,(255, 215, 0)),
        ('Butterfly Knife Gamma Doppler', 'Minimal Wear', 'No', 2199,(255, 215, 0)),
        ('Butterfly Knife Gamma Doppler', 'Factory New', 'StatTrak', 2200,(255, 215, 0)),
        ('Butterfly Knife Gamma Doppler', 'Minimal Wear', 'StatTrak', 2415,(255, 215, 0)),

        ('M9 Bayonet Gamma Doppler', 'Factory New', 'No', 9217,(255, 215, 0)),
        ('M9 Bayonet Gamma Doppler', 'Minimal Wear', 'No', 8700,(255, 215, 0)),
        ('M9 Bayonet Gamma Doppler', 'Factory New', 'StatTrak', 8310,(255, 215, 0)),
        ('M9 Bayonet Gamma Doppler', 'Minimal Wear', 'StatTrak', 7020,(255, 215, 0)),

        ('MP9 Starlight Protector', 'Factory New', 'No', 106,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Minimal Wear', 'No', 73,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Field-Tested', 'No', 69,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Well-Worn', 'No', 70,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Battle-Scarred', 'No', 71,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Factory New', 'StatTrak', 95,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Minimal Wear', 'StatTrak', 69,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Field-Tested', 'StatTrak', 61,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Well-Worn', 'StatTrak', 64,(235, 75, 75)),
        ('MP9 Starlight Protector', 'Battle-Scarred', 'StatTrak', 63,(235, 75, 75)),

        ('AK-47 Nightwish', 'Factory New', 'No', 150,(235, 75, 75)),
        ('AK-47 Nightwish', 'Minimal Wear', 'No', 75,(235, 75, 75)),
        ('AK-47 Nightwish', 'Field-Tested', 'No', 71,(235, 75, 75)),
        ('AK-47 Nightwish', 'Well-Worn', 'No', 67,(235, 75, 75)),
        ('AK-47 Nightwish', 'Battle-Scarred', 'No', 68,(235, 75, 75)),
        ('AK-47 Nightwish', 'Factory New', 'StatTrak', 139,(235, 75, 75)),
        ('AK-47 Nightwish', 'Minimal Wear', 'StatTrak', 70,(235, 75, 75)),
        ('AK-47 Nightwish', 'Field-Tested', 'StatTrak', 62,(235, 75, 75)),
        ('AK-47 Nightwish', 'Well-Worn', 'StatTrak', 62,(235, 75, 75)),
        ('AK-47 Nightwish', 'Battle-Scarred', 'StatTrak', 62,(235, 75, 75)),

        ('AK-47 Inheritance', 'Factory New', 'No', 170,(235, 75, 75)),
        ('AK-47 Inheritance', 'Minimal Wear', 'No', 83,(235, 75, 75)),
        ('AK-47 Inheritance', 'Field-Tested', 'No', 56,(235, 75, 75)),
        ('AK-47 Inheritance', 'Well-Worn', 'No', 54,(235, 75, 75)),
        ('AK-47 Inheritance', 'Battle-Scarred', 'No', 46,(235, 75, 75)),
        ('AK-47 Inheritance', 'Factory New', 'StatTrak', 371,(235, 75, 75)),
        ('AK-47 Inheritance', 'Minimal Wear', 'StatTrak', 192,(235, 75, 75)),
        ('AK-47 Inheritance', 'Field-Tested', 'StatTrak', 111,(235, 75, 75)),
        ('AK-47 Inheritance', 'Well-Worn', 'StatTrak', 101,(235, 75, 75)),
        ('AK-47 Inheritance', 'Battle-Scarred', 'StatTrak', 93,(235, 75, 75)),

        ('Desert Eagle Printstream', 'Factory New', 'No', 83,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Minimal Wear', 'No', 46,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Field-Tested', 'No', 38,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Well-Worn', 'No', 37,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Battle-Scarred', 'No', 35,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Factory New', 'StatTrak', 164,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Minimal Wear', 'StatTrak', 97,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Field-Tested', 'StatTrak', 64,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Well-Worn', 'StatTrak', 66,(235, 75, 75)),
        ('Desert Eagle Printstream', 'Battle-Scarred', 'StatTrak', 56,(235, 75, 75)),

        ('AK-47 Ice Coaled', 'Factory New', 'No', 17,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Minimal Wear', 'No', 8,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Field-Tested', 'No', 5,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Well-Worn', 'No', 6,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Battle-Scarred', 'No', 4,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Factory New', 'StatTrak', 39,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Minimal Wear', 'StatTrak', 21,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Field-Tested', 'StatTrak', 11,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Well-Worn', 'StatTrak', 14,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Battle-Scarred', 'StatTrak', 11,(211, 44, 230)),

        ('AWP Printstream', 'Factory New', 'No', 396,(235, 75, 75)),
        ('AWP Printstream', 'Minimal Wear', 'No', 103,(235, 75, 75)),
        ('AWP Printstream', 'Field-Tested', 'No', 55,(235, 75, 75)),
        ('AWP Printstream', 'Well-Worn', 'No', 47,(235, 75, 75)),
        ('AWP Printstream', 'Battle-Scarred', 'No', 45,(235, 75, 75)),
        ('AWP Printstream', 'Factory New', 'StatTrak', 597,(235, 75, 75)),
        ('AWP Printstream', 'Minimal Wear', 'StatTrak', 180,(235, 75, 75)),
        ('AWP Printstream', 'Field-Tested', 'StatTrak', 94,(235, 75, 75)),
        ('AWP Printstream', 'Well-Worn', 'StatTrak', 72,(235, 75, 75)),
        ('AWP Printstream', 'Battle-Scarred', 'StatTrak', 69,(235, 75, 75)),

        ('M4A4 Temukau', 'Factory New', 'No', 126,(235, 75, 75)),
        ('M4A4 Temukau', 'Minimal Wear', 'No', 59,(235, 75, 75)),
        ('M4A4 Temukau', 'Field-Tested', 'No', 35,(235, 75, 75)),
        ('M4A4 Temukau', 'Well-Worn', 'No', 33,(235, 75, 75)),
        ('M4A4 Temukau', 'Battle-Scarred', 'No', 29,(235, 75, 75)),
        ('M4A4 Temukau', 'Factory New', 'StatTrak', 201,(235, 75, 75)),
        ('M4A4 Temukau', 'Minimal Wear', 'StatTrak', 81,(235, 75, 75)),
        ('M4A4 Temukau', 'Field-Tested', 'StatTrak', 35,(235, 75, 75)),
        ('M4A4 Temukau', 'Well-Worn', 'StatTrak', 34,(235, 75, 75)),
        ('M4A4 Temukau', 'Battle-Scarred', 'StatTrak', 30,(235, 75, 75)),

        ('SSG 08 Dragonfire', 'Factory New', 'No', 513,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Minimal Wear', 'No', 364,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Field-Tested', 'No', 316,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Well-Worn', 'No', 300,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Battle-Scarred', 'No', 300,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Factory New', 'StatTrak', 167,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Minimal Wear', 'StatTrak', 114,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Field-Tested', 'StatTrak', 91,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Well-Worn', 'StatTrak', 90,(235, 75, 75)),
        ('SSG 08 Dragonfire', 'Battle-Scarred', 'StatTrak', 88,(235, 75, 75)),

        ('M4A1-S Fade', 'Factory New', 'No', 426,(235, 75, 75)),
        ('M4A1-S Fade', 'Minimal Wear', 'No', 445,(235, 75, 75)),

        ('AK-47 Asiimov', 'Factory New', 'No', 659,(235, 75, 75)),
        ('AK-47 Asiimov', 'Minimal Wear', 'No', 56,(235, 75, 75)),
        ('AK-47 Asiimov', 'Field-Tested', 'No', 41,(235, 75, 75)),
        ('AK-47 Asiimov', 'Well-Worn', 'No', 43,(235, 75, 75)),
        ('AK-47 Asiimov', 'Battle-Scarred', 'No', 40,(235, 75, 75)),
        ('AK-47 Asiimov', 'Factory New', 'StatTrak', 501,(235, 75, 75)),
        ('AK-47 Asiimov', 'Minimal Wear', 'StatTrak', 117,(235, 75, 75)),
        ('AK-47 Asiimov', 'Field-Tested', 'StatTrak', 67,(235, 75, 75)),
        ('AK-47 Asiimov', 'Well-Worn', 'StatTrak', 78,(235, 75, 75)),
        ('AK-47 Asiimov', 'Battle-Scarred', 'StatTrak', 65,(235, 75, 75)),

        ('AK-47 Elite Build', 'Factory New', 'No', 12,(75, 105, 255)),
        ('AK-47 Elite Build', 'Minimal Wear', 'No', 3,(75, 105, 255)),
        ('AK-47 Elite Build', 'Field-Tested', 'No', 2,(75, 105, 255)),
        ('AK-47 Elite Build', 'Well-Worn', 'No', 1,(75, 105, 255)),
        ('AK-47 Elite Build', 'Battle-Scarred', 'No', 1,(75, 105, 255)),
        ('AK-47 Elite Build', 'Factory New', 'StatTrak', 29,(75, 105, 255)),
        ('AK-47 Elite Build', 'Minimal Wear', 'StatTrak', 10,(75, 105, 255)),
        ('AK-47 Elite Build', 'Field-Tested', 'StatTrak', 6,(75, 105, 255)),
        ('AK-47 Elite Build', 'Well-Worn', 'StatTrak', 5,(75, 105, 255)),
        ('AK-47 Elite Build', 'Battle-Scarred', 'StatTrak', 4,(75, 105, 255)),

        ('Titan Katowice 2014', 'Holo', 'No', 69800,(136, 71, 255)),
        ('Titan Katowice  2014', 'Normal', 'No', 3546,(75, 105, 255)),

        ('iBUYPOWER Katowice 2014', 'Holo', 'No', 86000,(136, 71, 255)),
        ('iBUYPOWER Katowice  2014', 'Normal', 'No', 5146,(75, 105, 255)),

        ('Reason Gaming Katowice 2014', 'Holo', 'No', 53945,(136, 71, 255)),
        ('Reason Gaming Katowice  2014', 'Normal', 'No', 5800,(75, 105, 255)),

        ('Happy Boston 2018', 'Gold', 'No', 35900,(235, 75, 75)),

        ('Vox Eminor Katowice 2014', 'Holo', 'No', 30000,(136, 71, 255)),

        ('Team Dignitas Katowice 2014', 'Holo', 'No', 23561,(136, 71, 255)),

        ('Butterfly Knife Doppler Black Pearl', 'Factory New', 'No', 10875, (255, 215, 0)),
        ('Butterfly Knife Doppler Black Pearl', 'Minimal Wear', 'No', 15508, (255, 215, 0)),
        ('Butterfly Knife Doppler Black Pearl', 'Factory New', 'StatTrak', 13037, (255, 215, 0)),

        ('Butterfly Knife Doppler Ruby', 'Factory New', 'No', 11842, (255, 215, 0)),
        ('Butterfly Knife Doppler Ruby', 'Minimal Wear', 'No', 10787, (255, 215, 0)),
        ('Butterfly Knife Doppler Ruby', 'Factory New', 'StatTrak', 10794, (255, 215, 0)),
        ('Butterfly Knife Doppler Ruby', 'Minimal Wear', 'StatTrak', 15000, (255, 215, 0)),

        ('Karambit Gamma Doppler Emerald', 'Factory New', 'No', 9200, (255, 215, 0)),
        ('Karambit Gamma Doppler Emerald', 'Minimal Wear', 'No', 9139, (255, 215, 0)),
        ('Karambit Gamma Doppler Emerald', 'Factory New', 'StatTrak', 9120, (255, 215, 0)),
        ('Karambit Gamma Doppler Emerald', 'Minimal Wear', 'StatTrak', 13265, (255, 215, 0)),

        ('Natus Vincere Katowice 2014', 'Holo', 'No', 8640,(136, 71, 255)),

        ('M9 Bayonet Doppler Ruby', 'Factory New', 'No', 9050, (255, 215, 0)),
        ('M9 Bayonet Doppler Ruby', 'Minimal Wear', 'No', 8226, (255, 215, 0)),
        ('M9 Bayonet Doppler Ruby', 'Factory New', 'StatTrak', 8760, (255, 215, 0)),
        ('M9 Bayonet Doppler Ruby', 'Minimal Wear', 'StatTrak', 8899, (255, 215, 0)),

        ('AWP Gungnir', 'Factory New', 'No', 13151, (235, 75, 75)),
        ('AWP Gungnir', 'Minimal Wear', 'No', 11188, (235, 75, 75)),
        ('AWP Gungnir', 'Field-Tested', 'No', 8425, (235, 75, 75)),
        ('AWP Gungnir', 'Well-Worn', 'No', 7846, (235, 75, 75)),
        ('AWP Gungnir', 'Battle-Scarred', 'No', 7669, (235, 75, 75)),

        ('AWP Dragon Lore (Souvenir)', 'Factory New', 'No', 434232,(235, 75, 75)),
        ('AWP Dragon Lore (Souvenir)', 'Minimal Wear', 'No', 195404,(235, 75, 75)),
        ('AWP Dragon Lore (Souvenir)', 'Field-Tested', 'No', 44375,(235, 75, 75)),
        ('AWP Dragon Lore (Souvenir)', 'Battle-Scarred', 'No', 35533,(235, 75, 75)),

        ('AK-47 Wild Lotus', 'Factory New', 'No', 16452,(235, 75, 75)),
        ('AK-47 Wild Lotus', 'Minimal Wear', 'No', 11651,(235, 75, 75)),
        ('AK-47 Wild Lotus', 'Field-Tested', 'No', 8245,(235, 75, 75)),
        ('AK-47 Wild Lotus', 'Well-Worn', 'No', 5653,(235, 75, 75)),
        ('AK-47 Wild Lotus', 'Battle-Scarred', 'No', 4051,(235, 75, 75)),

        ('Sport Gloves Hedge Maze', 'Factory New', 'No', 28953,(255, 215, 0)),
        ('Sport Gloves Hedge Maze', 'Minimal Wear', 'No', 10133,(255, 215, 0)),
        ('Sport Gloves Hedge Maze', 'Field-Tested', 'No', 5900,(255, 215, 0)),
        ('Sport Gloves Hedge Maze', 'Well-Worn', 'No', 4516,(255, 215, 0)),
        ('Sport Gloves Hedge Maze', 'Battle-Scarred', 'No', 2833,(255, 215, 0)),

        ('Sport Gloves Pandora`s Box', 'Factory New', 'No', 29434,(255, 215, 0)),
        ('Sport Gloves Pandora`s Box', 'Minimal Wear', 'No', 8235,(255, 215, 0)),
        ('Sport Gloves Pandora`s Box', 'Field-Tested', 'No', 5550,(255, 215, 0)),
        ('Sport Gloves Pandora`s Box', 'Well-Worn', 'No', 4524,(255, 215, 0)),
        ('Sport Gloves Pandora`s Box', 'Battle-Scarred', 'No', 2815,(255, 215, 0)),

        ('M4A1-S Knight', 'Factory New', 'No', 3854,(211, 44, 230)),
        ('M4A1-S Knight', 'Minimal Wear', 'No', 4000,(211, 44, 230)),

        ('Glock-18 Fade', 'Factory New', 'No', 2013,(136, 71, 255)),
        ('Glock-18 Fade', 'Minimal Wear', 'No', 1997,(136, 71, 255)),

        ('AWP Medusa', 'Factory New', 'No', 4955,(235, 75, 75)),
        ('AWP Medusa', 'Minimal Wear', 'No', 2750,(235, 75, 75)),
        ('AWP Medusa', 'Field-Tested', 'No', 2229,(235, 75, 75)),
        ('AWP Medusa', 'Well-Worn', 'No', 1839,(235, 75, 75)),
        ('AWP Medusa', 'Battle-Scarred', 'No', 1845,(235, 75, 75)),

        ('Vox Eminor Katowice 2014', 'Normal', 'No', 1500,(75, 105, 255)),

        ('Driver Gloves Snow Leopard', 'Factory New', 'No', 2571,(255, 215, 0)),
        ('Driver Gloves Snow Leopard', 'Minimal Wear', 'No', 724,(255, 215, 0)),
        ('Driver Gloves Snow Leopard', 'Field-Tested', 'No', 364,(255, 215, 0)),
        ('Driver Gloves Snow Leopard', 'Well-Worn', 'No', 321,(255, 215, 0)),
        ('Driver Gloves Snow Leopard', 'Battle-Scarred', 'No', 285,(255, 215, 0)),


        ('Hydra Gloves Case Hardened', 'Factory New', 'No', 417,(255, 215, 0)),
        ('Hydra Gloves Case Hardened', 'Minimal Wear', 'No', 118,(255, 215, 0)),
        ('Hydra Gloves Case Hardened', 'Field-Tested', 'No', 77,(255, 215, 0)),
        ('Hydra Gloves Case Hardened', 'Well-Worn', 'No', 80,(255, 215, 0)),
        ('Hydra Gloves Case Hardened', 'Battle-Scarred', 'No', 76,(255, 215, 0)),

        ('Sport Gloves Amphibious', 'Factory New', 'No', 3256,(255, 215, 0)),
        ('Sport Gloves Amphibious', 'Minimal Wear', 'No', 970,(255, 215, 0)),
        ('Sport Gloves Amphibious', 'Field-Tested', 'No', 429,(255, 215, 0)),
        ('Sport Gloves Amphibious', 'Well-Worn', 'No', 371,(255, 215, 0)),
        ('Sport Gloves Amphibious', 'Battle-Scarred', 'No', 304,(255, 215, 0)),

        ('Sport Gloves Vice', 'Factory New', 'No', 9102,(255, 215, 0)),
        ('Sport Gloves Vice', 'Minimal Wear', 'No', 2107,(255, 215, 0)),
        ('Sport Gloves Vice', 'Field-Tested', 'No', 628,(255, 215, 0)),
        ('Sport Gloves Vice', 'Well-Worn', 'No', 537,(255, 215, 0)),
        ('Sport Gloves Vice', 'Battle-Scarred', 'No', 365,(255, 215, 0)),

        ('Driver Gloves Convoy', 'Factory New', 'No', 709,(255, 215, 0)),
        ('Driver Gloves Convoy', 'Minimal Wear', 'No', 567,(255, 215, 0)),
        ('Driver Gloves Convoy', 'Field-Tested', 'No', 416,(255, 215, 0)),
        ('Driver Gloves Convoy', 'Well-Worn', 'No', 106,(255, 215, 0)),
        ('Driver Gloves Convoy', 'Battle-Scarred', 'No', 88,(255, 215, 0)),

        ('AK-47 Redline', 'Minimal Wear', 'No', 197, (211, 44, 230)),
        ('AK-47 Redline', 'Field-Tested', 'No', 33, (211, 44, 230)),
        ('AK-47 Redline', 'Well-Worn', 'No', 29, (211, 44, 230)),
        ('AK-47 Redline', 'Battle-Scarred', 'No', 28, (211, 44, 230)),
        ('AK-47 Redline', 'Minimal Wear', 'StatTrak', 348, (211, 44, 230)),
        ('AK-47 Redline', 'Field-Tested', 'StatTrak', 71, (211, 44, 230)),
        ('AK-47 Redline', 'Well-Worn', 'StatTrak', 56, (211, 44, 230)),
        ('AK-47 Redline', 'Battle-Scarred', 'StatTrak', 54, (211, 44, 230)),

        ('Tec-9 Isaac', 'Factory New', 'No', 21,(75, 105, 255)),
        ('Tec-9 Isaac', 'Minimal Wear', 'No', 5,(75, 105, 255)),
        ('Tec-9 Isaac', 'Field-Tested', 'No', 3,(75, 105, 255)),
        ('Tec-9 Isaac', 'Well-Worn', 'No', 2,(75, 105, 255)),
        ('Tec-9 Isaac', 'Battle-Scarred', 'No', 2,(75, 105, 255)),
        ('Tec-9 Isaac', 'Factory New', 'StatTrak', 35,(75, 105, 255)),
        ('Tec-9 Isaac', 'Minimal Wear', 'StatTrak', 8,(75, 105, 255)),
        ('Tec-9 Isaac', 'Field-Tested', 'StatTrak', 4,(75, 105, 255)),
        ('Tec-9 Isaac', 'Well-Worn', 'StatTrak', 3,(75, 105, 255)),
        ('Tec-9 Isaac', 'Battle-Scarred', 'StatTrak', 3,(75, 105, 255)),

        ('AK-47 Elite Build', 'Factory New', 'No', 12,(75, 105, 255)),
        ('AK-47 Elite Build', 'Minimal Wear', 'No', 3,(75, 105, 255)),
        ('AK-47 Elite Build', 'Field-Tested', 'No', 2,(75, 105, 255)),
        ('AK-47 Elite Build', 'Well-Worn', 'No', 1,(75, 105, 255)),
        ('AK-47 Elite Build', 'Battle-Scarred', 'No', 1,(75, 105, 255)),
        ('AK-47 Elite Build', 'Factory New', 'StatTrak', 29,(75, 105, 255)),
        ('AK-47 Elite Build', 'Minimal Wear', 'StatTrak', 10,(75, 105, 255)),
        ('AK-47 Elite Build', 'Field-Tested', 'StatTrak', 6,(75, 105, 255)),
        ('AK-47 Elite Build', 'Well-Worn', 'StatTrak', 5,(75, 105, 255)),
        ('AK-47 Elite Build', 'Battle-Scarred', 'StatTrak', 4,(75, 105, 255)),

        ('M4A1-S Fade', 'Factory New', 'No', 426,(235, 75, 75)),
        ('M4A1-S Fade', 'Minimal Wear', 'No', 445,(235, 75, 75)),

        ('AK-47 Ice Coaled', 'Factory New', 'No', 17,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Minimal Wear', 'No', 8,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Field-Tested', 'No', 5,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Well-Worn', 'No', 6,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Battle-Scarred', 'No', 4,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Factory New', 'StatTrak', 39,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Minimal Wear', 'StatTrak', 21,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Field-Tested', 'StatTrak', 11,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Well-Worn', 'StatTrak', 14,(211, 44, 230)),
        ('AK-47 Ice Coaled', 'Battle-Scarred', 'StatTrak', 11,(211, 44, 230)),

        ('AWP Dragon Lore', 'Factory New', 'No', 12007,(235, 75, 75)),
        ('AWP Dragon Lore', 'Minimal Wear', 'No', 9229,(235, 75, 75)),
        ('AWP Dragon Lore', 'Field-Tested', 'No', 6600,(235, 75, 75)),
        ('AWP Dragon Lore', 'Well-Worn', 'No', 5889,(235, 75, 75)),
        ('AWP Dragon Lore', 'Battle-Scarred', 'No', 4900,(235, 75, 75)),

        ('M4A4 Howl', 'Factory New', 'No', 7070,(255, 215, 0)),
        ('M4A4 Howl', 'Minimal Wear', 'No', 5224,(255, 215, 0)),
        ('M4A4 Howl', 'Field-Tested', 'No', 4422,(255, 215, 0)),
        ('M4A4 Howl', 'Well-Worn', 'No', 4123,(255, 215, 0)),
        ('M4A4 Howl', 'Factory New', 'StatTrak', 15149,(255, 215, 0)),
        ('M4A4 Howl', 'Minimal Wear', 'StatTrak', 9494,(255, 215, 0)),
        ('M4A4 Howl', 'Field-Tested', 'StatTrak', 7854,(255, 215, 0)),
        ('M4A4 Howl', 'Well-Worn', 'StatTrak', 7237,(255, 215, 0)),

        ('M4A4 Temukau', 'Factory New', 'No', 126,(235, 75, 75)),
        ('M4A4 Temukau', 'Minimal Wear', 'No', 59,(235, 75, 75)),
        ('M4A4 Temukau', 'Field-Tested', 'No', 35,(235, 75, 75)),
        ('M4A4 Temukau', 'Well-Worn', 'No', 33,(235, 75, 75)),
        ('M4A4 Temukau', 'Battle-Scarred', 'No', 29,(235, 75, 75)),
        ('M4A4 Temukau', 'Factory New', 'StatTrak', 201,(235, 75, 75)),
        ('M4A4 Temukau', 'Minimal Wear', 'StatTrak', 81,(235, 75, 75)),
        ('M4A4 Temukau', 'Field-Tested', 'StatTrak', 35,(235, 75, 75)),
        ('M4A4 Temukau', 'Well-Worn', 'StatTrak', 34,(235, 75, 75)),
        ('M4A4 Temukau', 'Battle-Scarred', 'StatTrak', 30,(235, 75, 75)),

        ('M4A4 Evil Daimyo', 'Factory New', 'No', 10,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Minimal Wear', 'No', 4,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Field-Tested', 'No', 3,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Well-Worn', 'No', 3,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Battle-Scarred', 'No', 3,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Factory New', 'StatTrak', 20,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Minimal Wear', 'StatTrak', 11,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Field-Tested', 'StatTrak', 8,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Well-Worn', 'StatTrak', 8,(136, 71, 255)),
        ('M4A4 Evil Daimyo', 'Battle-Scarred', 'StatTrak', 8,(136, 71, 255)),

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
        self.MAX_PRICE = 999999
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
        return f"case_10000_{animation_number}_({combination.price})_2.webp"

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