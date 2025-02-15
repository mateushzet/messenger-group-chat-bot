CREATE TABLE skin_prices (
    skin_name VARCHAR(255),
    condition VARCHAR(50),
    stattrak_status VARCHAR(50),
    price INT
);

select * from skin_prices

INSERT INTO skin_prices (skin_name, condition, stattrak_status, price)
VALUES
-- AK-47 Wasteland Rebel
('AK-47 Wasteland Rebel', 'Factory New', 'No', 184),
('AK-47 Wasteland Rebel', 'Minimal Wear', 'No', 45),
('AK-47 Wasteland Rebel', 'Field-Tested', 'No', 27),
('AK-47 Wasteland Rebel', 'Well-Worn', 'No', 35),
('AK-47 Wasteland Rebel', 'Battle-Scarred', 'No', 26),
('AK-47 Wasteland Rebel', 'Factory New', 'StatTrak', 1054),
('AK-47 Wasteland Rebel', 'Minimal Wear', 'StatTrak', 120),
('AK-47 Wasteland Rebel', 'Field-Tested', 'StatTrak', 88),
('AK-47 Wasteland Rebel', 'Well-Worn', 'StatTrak', 100),
('AK-47 Wasteland Rebel', 'Battle-Scarred', 'StatTrak', 99),

-- AWP Asiimov
('AWP Asiimov', 'Field-Tested', 'No', 133),
('AWP Asiimov', 'Well-Worn', 'No', 100),
('AWP Asiimov', 'Battle-Scarred', 'No', 72),
('AWP Asiimov', 'Field-Tested', 'StatTrak', 225),
('AWP Asiimov', 'Well-Worn', 'StatTrak', 165),
('AWP Asiimov', 'Battle-Scarred', 'StatTrak', 122),

-- AUG Chameleon
('AUG Chameleon', 'Factory New', 'No', 4),
('AUG Chameleon', 'Minimal Wear', 'No', 2),
('AUG Chameleon', 'Field-Tested', 'No', 2),
('AUG Chameleon', 'Well-Worn', 'No', 3),
('AUG Chameleon', 'Battle-Scarred', 'No', 3),
('AUG Chameleon', 'Factory New', 'StatTrak', 15),
('AUG Chameleon', 'Minimal Wear', 'StatTrak', 8),
('AUG Chameleon', 'Field-Tested', 'StatTrak', 7),
('AUG Chameleon', 'Well-Worn', 'StatTrak', 9),
('AUG Chameleon', 'Battle-Scarred', 'StatTrak', 9),

-- AK-47 Redline
('AK-47 Redline', 'Minimal Wear', 'No', 147),
('AK-47 Redline', 'Field-Tested', 'No', 28),
('AK-47 Redline', 'Well-Worn', 'No', 21),
('AK-47 Redline', 'Battle-Scarred', 'No', 19),
('AK-47 Redline', 'Minimal Wear', 'StatTrak', 310),
('AK-47 Redline', 'Field-Tested', 'StatTrak', 72),
('AK-47 Redline', 'Well-Worn', 'StatTrak', 43),
('AK-47 Redline', 'Battle-Scarred', 'StatTrak', 35),

-- SG 553 Pulse
('SG 553 Pulse', 'Minimal Wear', 'No', 5),
('SG 553 Pulse', 'Field-Tested', 'No', 3),
('SG 553 Pulse', 'Well-Worn', 'No', 2),
('SG 553 Pulse', 'Battle-Scarred', 'No', 2),
('SG 553 Pulse', 'Minimal Wear', 'StatTrak', 10),
('SG 553 Pulse', 'Field-Tested', 'StatTrak', 5),
('SG 553 Pulse', 'Well-Worn', 'StatTrak', 4),
('SG 553 Pulse', 'Battle-Scarred', 'StatTrak', 5),

-- USP-S Guardian
('USP-S Guardian', 'Factory New', 'No', 7),
('USP-S Guardian', 'Minimal Wear', 'No', 5),
('USP-S Guardian', 'Field-Tested', 'No', 3),
('USP-S Guardian', 'Factory New', 'StatTrak', 13),
('USP-S Guardian', 'Minimal Wear', 'StatTrak', 9),
('USP-S Guardian', 'Field-Tested', 'StatTrak', 9),

-- MAG-7 Heaven Guard
('MAG-7 Heaven Guard', 'Factory New', 'No', 1),
('MAG-7 Heaven Guard', 'Minimal Wear', 'No', 1),
('MAG-7 Heaven Guard', 'Field-Tested', 'No', 1),
('MAG-7 Heaven Guard', 'Well-Worn', 'No', 1),
('MAG-7 Heaven Guard', 'Factory New', 'StatTrak', 1),
('MAG-7 Heaven Guard', 'Minimal Wear', 'StatTrak', 1),
('MAG-7 Heaven Guard', 'Field-Tested', 'StatTrak', 1),
('MAG-7 Heaven Guard', 'Well-Worn', 'StatTrak', 2),

-- M4A4 Griffin
('M4A4 Griffin', 'Factory New', 'No', 6),
('M4A4 Griffin', 'Minimal Wear', 'No', 3),
('M4A4 Griffin', 'Field-Tested', 'No', 2),
('M4A4 Griffin', 'Well-Worn', 'No', 3),
('M4A4 Griffin', 'Battle-Scarred', 'No', 2),
('M4A4 Griffin', 'Factory New', 'StatTrak', 16),
('M4A4 Griffin', 'Minimal Wear', 'StatTrak', 7),
('M4A4 Griffin', 'Field-Tested', 'StatTrak', 5),
('M4A4 Griffin', 'Well-Worn', 'StatTrak', 7),
('M4A4 Griffin', 'Battle-Scarred', 'StatTrak', 5),

-- Tec-9 Sandstorm
('Tec-9 Sandstorm', 'Minimal Wear', 'No', 2),
('Tec-9 Sandstorm', 'Field-Tested', 'No', 1),
('Tec-9 Sandstorm', 'Well-Worn', 'No', 1),
('Tec-9 Sandstorm', 'Battle-Scarred', 'No', 1),
('Tec-9 Sandstorm', 'Minimal Wear', 'StatTrak', 3),
('Tec-9 Sandstorm', 'Field-Tested', 'StatTrak', 1),
('Tec-9 Sandstorm', 'Well-Worn', 'StatTrak', 1),
('Tec-9 Sandstorm', 'Battle-Scarred', 'StatTrak', 1),

-- P2000 Fire Elemental
('P2000 Fire Elemental', 'Factory New', 'No', 21),
('P2000 Fire Elemental', 'Minimal Wear', 'No', 11),
('P2000 Fire Elemental', 'Field-Tested', 'No', 9),
('P2000 Fire Elemental', 'Well-Worn', 'No', 10),
('P2000 Fire Elemental', 'Battle-Scarred', 'No', 8),
('P2000 Fire Elemental', 'Factory New', 'StatTrak', 138),
('P2000 Fire Elemental', 'Minimal Wear', 'StatTrak', 64),
('P2000 Fire Elemental', 'Field-Tested', 'StatTrak', 40),
('P2000 Fire Elemental', 'Well-Worn', 'StatTrak', 63),
('P2000 Fire Elemental', 'Battle-Scarred', 'StatTrak', 50),

-- M4A1-S Cyrex
('M4A1-S Cyrex', 'Factory New', 'No', 39),
('M4A1-S Cyrex', 'Minimal Wear', 'No', 28),
('M4A1-S Cyrex', 'Field-Tested', 'No', 19),
('M4A1-S Cyrex', 'Well-Worn', 'No', 20),
('M4A1-S Cyrex', 'Battle-Scarred', 'No', 18),
('M4A1-S Cyrex', 'Factory New', 'StatTrak', 118),
('M4A1-S Cyrex', 'Minimal Wear', 'StatTrak', 87),
('M4A1-S Cyrex', 'Field-Tested', 'StatTrak', 50),
('M4A1-S Cyrex', 'Well-Worn', 'StatTrak', 53),
('M4A1-S Cyrex', 'Battle-Scarred', 'StatTrak', 58),

-- P90 Asiimov
('P90 Asiimov', 'Factory New', 'No', 30),
('P90 Asiimov', 'Minimal Wear', 'No', 13),
('P90 Asiimov', 'Field-Tested', 'No', 6),
('P90 Asiimov', 'Well-Worn', 'No', 6),
('P90 Asiimov', 'Battle-Scarred', 'No', 6),
('P90 Asiimov', 'Factory New', 'StatTrak', 161),
('P90 Asiimov', 'Minimal Wear', 'StatTrak', 49),
('P90 Asiimov', 'Field-Tested', 'StatTrak', 24),
('P90 Asiimov', 'Well-Worn', 'StatTrak', 20),
('P90 Asiimov', 'Battle-Scarred', 'StatTrak', 22),

-- Glock-18 Water Elemental
('Glock-18 Water Elemental', 'Factory New', 'No', 11),
('Glock-18 Water Elemental', 'Minimal Wear', 'No', 7),
('Glock-18 Water Elemental', 'Field-Tested', 'No', 4),
('Glock-18 Water Elemental', 'Well-Worn', 'No', 4),
('Glock-18 Water Elemental', 'Battle-Scarred', 'No', 4),
('Glock-18 Water Elemental', 'Factory New', 'StatTrak', 45),
('Glock-18 Water Elemental', 'Minimal Wear', 'StatTrak', 25),
('Glock-18 Water Elemental', 'Field-Tested', 'StatTrak', 15),
('Glock-18 Water Elemental', 'Well-Worn', 'StatTrak', 18),
('Glock-18 Water Elemental', 'Battle-Scarred', 'StatTrak', 15),

-- CZ75-Auto Tigris
('CZ75-Auto Tigris', 'Factory New', 'No', 2),
('CZ75-Auto Tigris', 'Minimal Wear', 'No', 1),
('CZ75-Auto Tigris', 'Field-Tested', 'No', 1),
('CZ75-Auto Tigris', 'Well-Worn', 'No', 1),
('CZ75-Auto Tigris', 'Battle-Scarred', 'No', 1),
('CZ75-Auto Tigris', 'Factory New', 'StatTrak', 4),
('CZ75-Auto Tigris', 'Minimal Wear', 'StatTrak', 2),
('CZ75-Auto Tigris', 'Field-Tested', 'StatTrak', 1),
('CZ75-Auto Tigris', 'Well-Worn', 'StatTrak', 1),
('CZ75-Auto Tigris', 'Battle-Scarred', 'StatTrak', 1),

-- PP-Bizon Osiris
('PP-Bizon Osiris', 'Factory New', 'No', 1),
('PP-Bizon Osiris', 'Minimal Wear', 'No', 1),
('PP-Bizon Osiris', 'Field-Tested', 'No', 1),
('PP-Bizon Osiris', 'Well-Worn', 'No', 1),
('PP-Bizon Osiris', 'Battle-Scarred', 'No', 1),
('PP-Bizon Osiris', 'Factory New', 'StatTrak', 4),
('PP-Bizon Osiris', 'Minimal Wear', 'StatTrak', 2),
('PP-Bizon Osiris', 'Field-Tested', 'StatTrak', 2),
('PP-Bizon Osiris', 'Well-Worn', 'StatTrak', 2),
('PP-Bizon Osiris', 'Battle-Scarred', 'StatTrak', 1),

-- Nova Koi
('Nova Koi', 'Factory New', 'No', 1),
('Nova Koi', 'Minimal Wear', 'No', 1),
('Nova Koi', 'Field-Tested', 'No', 1),
('Nova Koi', 'Factory New', 'StatTrak', 4),
('Nova Koi', 'Minimal Wear', 'StatTrak', 2),
('Nova Koi', 'Field-Tested', 'StatTrak', 2),

-- MP7 Urban Hazard
('MP7 Urban Hazard', 'Factory New', 'No', 1),
('MP7 Urban Hazard', 'Minimal Wear', 'No', 1),
('MP7 Urban Hazard', 'Field-Tested', 'No', 1),
('MP7 Urban Hazard', 'Well-Worn', 'No', 1),
('MP7 Urban Hazard', 'Battle-Scarred', 'No', 1),
('MP7 Urban Hazard', 'Factory New', 'StatTrak', 1),
('MP7 Urban Hazard', 'Minimal Wear', 'StatTrak', 1),
('MP7 Urban Hazard', 'Field-Tested', 'StatTrak', 1),
('MP7 Urban Hazard', 'Well-Worn', 'StatTrak', 1),
('MP7 Urban Hazard', 'Battle-Scarred', 'StatTrak', 1),

-- SSG 08 Abyss
('SSG 08 Abyss', 'Factory New', 'No', 2),
('SSG 08 Abyss', 'Minimal Wear', 'No', 1),
('SSG 08 Abyss', 'Field-Tested', 'No', 1),
('SSG 08 Abyss', 'Well-Worn', 'No', 1),
('SSG 08 Abyss', 'Battle-Scarred', 'No', 1),
('SSG 08 Abyss', 'Factory New', 'StatTrak', 9),
('SSG 08 Abyss', 'Minimal Wear', 'StatTrak', 2),
('SSG 08 Abyss', 'Field-Tested', 'StatTrak', 1),
('SSG 08 Abyss', 'Well-Worn', 'StatTrak', 1),
('SSG 08 Abyss', 'Battle-Scarred', 'StatTrak', 1),

-- M4A1-S Bright Water
('M4A1-S Bright Water', 'Minimal Wear', 'No', 27),
('M4A1-S Bright Water', 'Field-Tested', 'No', 27),
('M4A1-S Bright Water', 'Minimal Wear', 'StatTrak', 69),
('M4A1-S Bright Water', 'Field-Tested', 'StatTrak', 62),

-- AK-47 Fire Serpent
('AK-47 Fire Serpent', 'Factory New', 'No', 2143),
('AK-47 Fire Serpent', 'Minimal Wear', 'No', 1125),
('AK-47 Fire Serpent', 'Field-Tested', 'No', 774),
('AK-47 Fire Serpent', 'Well-Worn', 'No', 703),
('AK-47 Fire Serpent', 'Battle-Scarred', 'No', 469),
('AK-47 Fire Serpent', 'Factory New', 'StatTrak', 4436),
('AK-47 Fire Serpent', 'Minimal Wear', 'StatTrak', 2744),
('AK-47 Fire Serpent', 'Field-Tested', 'StatTrak', 1672),
('AK-47 Fire Serpent', 'Well-Worn', 'StatTrak', 1293),
('AK-47 Fire Serpent', 'Battle-Scarred', 'StatTrak', 1012),

-- AK-47 Vulcan
('AK-47 Vulcan', 'Factory New', 'No', 706),
('AK-47 Vulcan', 'Minimal Wear', 'No', 443),
('AK-47 Vulcan', 'Field-Tested', 'No', 226),
('AK-47 Vulcan', 'Well-Worn', 'No', 148),
('AK-47 Vulcan', 'Battle-Scarred', 'No', 136),
('AK-47 Vulcan', 'Factory New', 'StatTrak', 1317),
('AK-47 Vulcan', 'Minimal Wear', 'StatTrak', 785),
('AK-47 Vulcan', 'Field-Tested', 'StatTrak', 349),
('AK-47 Vulcan', 'Well-Worn', 'StatTrak', 226),
('AK-47 Vulcan', 'Battle-Scarred', 'StatTrak', 162),

-- AUG Torque
('AUG Torque', 'Factory New', 'No', 9),
('AUG Torque', 'Minimal Wear', 'No', 9),
('AUG Torque', 'Field-Tested', 'No', 8),
('AUG Torque', 'Well-Worn', 'No', 7),
('AUG Torque', 'Battle-Scarred', 'No', 7),
('AUG Torque', 'Factory New', 'StatTrak', 16),
('AUG Torque', 'Minimal Wear', 'StatTrak', 13),
('AUG Torque', 'Field-Tested', 'StatTrak', 10),
('AUG Torque', 'Well-Worn', 'StatTrak', 11),
('AUG Torque', 'Battle-Scarred', 'StatTrak', 11),

-- Tec-9 Isaac
('Tec-9 Isaac', 'Factory New', 'No', 11),
('Tec-9 Isaac', 'Minimal Wear', 'No', 4),
('Tec-9 Isaac', 'Field-Tested', 'No', 3),
('Tec-9 Isaac', 'Well-Worn', 'No', 2),
('Tec-9 Isaac', 'Battle-Scarred', 'No', 2),
('Tec-9 Isaac', 'Factory New', 'StatTrak', 26),
('Tec-9 Isaac', 'Minimal Wear', 'StatTrak', 6),
('Tec-9 Isaac', 'Field-Tested', 'StatTrak', 3),
('Tec-9 Isaac', 'Well-Worn', 'StatTrak', 2),
('Tec-9 Isaac', 'Battle-Scarred', 'StatTrak', 2),

-- P90 Module
('P90 Module', 'Factory New', 'No', 2),
('P90 Module', 'Minimal Wear', 'No', 2),
('P90 Module', 'Field-Tested', 'No', 2),
('P90 Module', 'Factory New', 'StatTrak', 3),
('P90 Module', 'Minimal Wear', 'StatTrak', 2),
('P90 Module', 'Field-Tested', 'StatTrak', 2),

-- P2000 Pulse
('P2000 Pulse', 'Factory New', 'No', 2),
('P2000 Pulse', 'Minimal Wear', 'No', 2),
('P2000 Pulse', 'Field-Tested', 'No', 2),
('P2000 Pulse', 'Well-Worn', 'No', 2),
('P2000 Pulse', 'Battle-Scarred', 'No', 2),
('P2000 Pulse', 'Factory New', 'StatTrak', 3),
('P2000 Pulse', 'Minimal Wear', 'StatTrak', 2),
('P2000 Pulse', 'Field-Tested', 'StatTrak', 2),
('P2000 Pulse', 'Well-Worn', 'StatTrak', 2),
('P2000 Pulse', 'Battle-Scarred', 'StatTrak', 1),

-- SSG 08 Slashed
('SSG 08 Slashed', 'Field-Tested', 'No', 2),
('SSG 08 Slashed', 'Well-Worn', 'No', 1),
('SSG 08 Slashed', 'Battle-Scarred', 'No', 2),
('SSG 08 Slashed', 'Field-Tested', 'StatTrak', 2),
('SSG 08 Slashed', 'Well-Worn', 'StatTrak', 2),
('SSG 08 Slashed', 'Battle-Scarred', 'StatTrak', 2),

-- AK-47 Aquamarine Revenge
('AK-47 Aquamarine Revenge', 'Factory New', 'No', 121),
('AK-47 Aquamarine Revenge', 'Minimal Wear', 'No', 64),
('AK-47 Aquamarine Revenge', 'Field-Tested', 'No', 32),
('AK-47 Aquamarine Revenge', 'Well-Worn', 'No', 20),
('AK-47 Aquamarine Revenge', 'Battle-Scarred', 'No', 21),
('AK-47 Aquamarine Revenge', 'Factory New', 'StatTrak', 217),
('AK-47 Aquamarine Revenge', 'Minimal Wear', 'StatTrak', 124),
('AK-47 Aquamarine Revenge', 'Field-Tested', 'StatTrak', 74),
('AK-47 Aquamarine Revenge', 'Well-Worn', 'StatTrak', 51),
('AK-47 Aquamarine Revenge', 'Battle-Scarred', 'StatTrak', 49),

-- AWP Hyper Beast
('AWP Hyper Beast', 'Factory New', 'No', 81),
('AWP Hyper Beast', 'Minimal Wear', 'No', 42),
('AWP Hyper Beast', 'Field-Tested', 'No', 23),
('AWP Hyper Beast', 'Well-Worn', 'No', 21),
('AWP Hyper Beast', 'Battle-Scarred', 'No', 20),
('AWP Hyper Beast', 'Factory New', 'StatTrak', 210),
('AWP Hyper Beast', 'Minimal Wear', 'StatTrak', 104),
('AWP Hyper Beast', 'Field-Tested', 'StatTrak', 58),
('AWP Hyper Beast', 'Well-Worn', 'StatTrak', 54),
('AWP Hyper Beast', 'Battle-Scarred', 'StatTrak', 54),

-- M4A4 Evil Daimyo
('M4A4 Evil Daimyo', 'Factory New', 'No', 5),
('M4A4 Evil Daimyo', 'Minimal Wear', 'No', 3),
('M4A4 Evil Daimyo', 'Field-Tested', 'No', 2),
('M4A4 Evil Daimyo', 'Well-Worn', 'No', 2),
('M4A4 Evil Daimyo', 'Battle-Scarred', 'No', 1),
('M4A4 Evil Daimyo', 'Factory New', 'StatTrak', 15),
('M4A4 Evil Daimyo', 'Minimal Wear', 'StatTrak', 8),
('M4A4 Evil Daimyo', 'Field-Tested', 'StatTrak', 5),
('M4A4 Evil Daimyo', 'Well-Worn', 'StatTrak', 6),
('M4A4 Evil Daimyo', 'Battle-Scarred', 'StatTrak', 5),

-- USP-S Torque
('USP-S Torque', 'Factory New', 'No', 2),
('USP-S Torque', 'Minimal Wear', 'No', 1),
('USP-S Torque', 'Field-Tested', 'No', 1),
('USP-S Torque', 'Well-Worn', 'No', 1),
('USP-S Torque', 'Battle-Scarred', 'No', 1),
('USP-S Torque', 'Factory New', 'StatTrak', 4),
('USP-S Torque', 'Minimal Wear', 'StatTrak', 3),
('USP-S Torque', 'Field-Tested', 'StatTrak', 2),
('USP-S Torque', 'Well-Worn', 'StatTrak', 2),
('USP-S Torque', 'Battle-Scarred', 'StatTrak', 3),

-- Karambit Safari Mesh
('Karambit Safari Mesh', 'Factory New', 'No', 823),
('Karambit Safari Mesh', 'Minimal Wear', 'No', 586),
('Karambit Safari Mesh', 'Field-Tested', 'No', 559),
('Karambit Safari Mesh', 'Well-Worn', 'No', 541),
('Karambit Safari Mesh', 'Battle-Scarred', 'No', 569),
('Karambit Safari Mesh', 'Minimal Wear', 'StatTrak', 576),
('Karambit Safari Mesh', 'Field-Tested', 'StatTrak', 563),
('Karambit Safari Mesh', 'Well-Worn', 'StatTrak', 583),
('Karambit Safari Mesh', 'Battle-Scarred', 'StatTrak', 562),

-- Butterfly Knife Fade
('Butterfly Knife Fade', 'Factory New', 'No', 3372),
('Butterfly Knife Fade', 'Minimal Wear', 'No', 3000),
('Butterfly Knife Fade', 'Factory New', 'StatTrak', 3156),
('Butterfly Knife Fade', 'Minimal Wear', 'StatTrak', 3238),

-- Butterfly Knife Ultraviolet
('Butterfly Knife Ultraviolet', 'Factory New', 'No', 2150),
('Butterfly Knife Ultraviolet', 'Minimal Wear', 'No', 1146),
('Butterfly Knife Ultraviolet', 'Field-Tested', 'No', 939),
('Butterfly Knife Ultraviolet', 'Well-Worn', 'No', 878),
('Butterfly Knife Ultraviolet', 'Battle-Scarred', 'No', 772),
('Butterfly Knife Ultraviolet', 'Factory New', 'StatTrak', 6000),
('Butterfly Knife Ultraviolet', 'Minimal Wear', 'StatTrak', 1130),
('Butterfly Knife Ultraviolet', 'Field-Tested', 'StatTrak', 892),
('Butterfly Knife Ultraviolet', 'Well-Worn', 'StatTrak', 864),
('Butterfly Knife Ultraviolet', 'Battle-Scarred', 'StatTrak', 768),

-- Bayonet Slaughter
('Bayonet Slaughter', 'Factory New', 'No', 541),
('Bayonet Slaughter', 'Minimal Wear', 'No', 450),
('Bayonet Slaughter', 'Field-Tested', 'No', 400),
('Bayonet Slaughter', 'Factory New', 'StatTrak', 590),
('Bayonet Slaughter', 'Minimal Wear', 'StatTrak', 543),
('Bayonet Slaughter', 'Field-Tested', 'StatTrak', 429),

-- Bayonet Urban Masked
('Bayonet Urban Masked', 'Factory New', 'No', 337),
('Bayonet Urban Masked', 'Minimal Wear', 'No', 226),
('Bayonet Urban Masked', 'Field-Tested', 'No', 190),
('Bayonet Urban Masked', 'Well-Worn', 'No', 186),
('Bayonet Urban Masked', 'Battle-Scarred', 'No', 185),
('Bayonet Urban Masked', 'Minimal Wear', 'StatTrak', 240),
('Bayonet Urban Masked', 'Field-Tested', 'StatTrak', 196),
('Bayonet Urban Masked', 'Well-Worn', 'StatTrak', 192),
('Bayonet Urban Masked', 'Battle-Scarred', 'StatTrak', 192),

-- Falchion Knife Case Hardened
('Falchion Knife Case Hardened', 'Factory New', 'No', 356),
('Falchion Knife Case Hardened', 'Minimal Wear', 'No', 239),
('Falchion Knife Case Hardened', 'Field-Tested', 'No', 209),
('Falchion Knife Case Hardened', 'Well-Worn', 'No', 180),
('Falchion Knife Case Hardened', 'Battle-Scarred', 'No', 165),
('Falchion Knife Case Hardened', 'Factory New', 'StatTrak', 412),
('Falchion Knife Case Hardened', 'Minimal Wear', 'StatTrak', 274),
('Falchion Knife Case Hardened', 'Field-Tested', 'StatTrak', 240),
('Falchion Knife Case Hardened', 'Well-Worn', 'StatTrak', 206),
('Falchion Knife Case Hardened', 'Battle-Scarred', 'StatTrak', 218),

-- Gut Knife Freehand
('Gut Knife Freehand', 'Factory New', 'No', 121),
('Gut Knife Freehand', 'Minimal Wear', 'No', 119),
('Gut Knife Freehand', 'Field-Tested', 'No', 116),
('Gut Knife Freehand', 'Well-Worn', 'No', 115),
('Gut Knife Freehand', 'Battle-Scarred', 'No', 109),
('Gut Knife Freehand', 'Factory New', 'StatTrak', 145),
('Gut Knife Freehand', 'Minimal Wear', 'StatTrak', 122),
('Gut Knife Freehand', 'Field-Tested', 'StatTrak', 117),
('Gut Knife Freehand', 'Well-Worn', 'StatTrak', 154),
('Gut Knife Freehand', 'Battle-Scarred', 'StatTrak', 343),

-- Flip Knife Lore
('Flip Knife Lore', 'Factory New', 'No', 439),
('Flip Knife Lore', 'Minimal Wear', 'No', 335),
('Flip Knife Lore', 'Field-Tested', 'No', 269),
('Flip Knife Lore', 'Well-Worn', 'No', 260),
('Flip Knife Lore', 'Battle-Scarred', 'No', 229),
('Flip Knife Lore', 'Factory New', 'StatTrak', 438),
('Flip Knife Lore', 'Minimal Wear', 'StatTrak', 340),
('Flip Knife Lore', 'Field-Tested', 'StatTrak', 273),
('Flip Knife Lore', 'Well-Worn', 'StatTrak', 298),
('Flip Knife Lore', 'Battle-Scarred', 'StatTrak', 263),

-- Huntsman Knife Marble Fade
('Huntsman Knife Marble Fade', 'Factory New', 'No', 318),
('Huntsman Knife Marble Fade', 'Minimal Wear', 'No', 330),
('Huntsman Knife Marble Fade', 'Factory New', 'StatTrak', 354),
('Huntsman Knife Marble Fade', 'Minimal Wear', 'StatTrak', 714),

-- Huntsman Knife Scorched
('Huntsman Knife Scorched', 'Factory New', 'No', 259),
('Huntsman Knife Scorched', 'Minimal Wear', 'No', 129),
('Huntsman Knife Scorched', 'Field-Tested', 'No', 121),
('Huntsman Knife Scorched', 'Well-Worn', 'No', 100),
('Huntsman Knife Scorched', 'Battle-Scarred', 'No', 101),
('Huntsman Knife Scorched', 'Minimal Wear', 'StatTrak', 153),
('Huntsman Knife Scorched', 'Field-Tested', 'StatTrak', 133),
('Huntsman Knife Scorched', 'Well-Worn', 'StatTrak', 143),
('Huntsman Knife Scorched', 'Battle-Scarred', 'StatTrak', 197),

-- Karambit Tiger Tooth
('Karambit Tiger Tooth', 'Factory New', 'No', 1230),
('Karambit Tiger Tooth', 'Minimal Wear', 'No', 1193),
('Karambit Tiger Tooth', 'Factory New', 'StatTrak', 1161),
('Karambit Tiger Tooth', 'Minimal Wear', 'StatTrak', 1199),

-- AWP Dragon Lore
('AWP Dragon Lore', 'Factory New', 'No', 11173),
('AWP Dragon Lore', 'Minimal Wear', 'No', 8632),
('AWP Dragon Lore', 'Field-Tested', 'No', 6071),
('AWP Dragon Lore', 'Well-Worn', 'No', 5213),
('AWP Dragon Lore', 'Battle-Scarred', 'No', 4273),

-- AK-47 Gold Arabesque
('AK-47 Gold Arabesque', 'Factory New', 'No', 2740),
('AK-47 Gold Arabesque', 'Minimal Wear', 'No', 2303),
('AK-47 Gold Arabesque', 'Field-Tested', 'No', 1888),
('AK-47 Gold Arabesque', 'Well-Worn', 'No', 1611),
('AK-47 Gold Arabesque', 'Battle-Scarred', 'No', 1424),

-- M4A4 Howl
('M4A4 Howl', 'Factory New', 'No', 6131),
('M4A4 Howl', 'Minimal Wear', 'No', 4606),
('M4A4 Howl', 'Field-Tested', 'No', 3958),
('M4A4 Howl', 'Well-Worn', 'No', 3768),
('M4A4 Howl', 'Factory New', 'StatTrak', 12400),
('M4A4 Howl', 'Minimal Wear', 'StatTrak', 8779),
('M4A4 Howl', 'Field-Tested', 'StatTrak', 6387),
('M4A4 Howl', 'Well-Worn', 'StatTrak', 7321),

-- Butterfly Knife Gamma Doppler
('Butterfly Knife Gamma Doppler', 'Factory New', 'No', 3004),
('Butterfly Knife Gamma Doppler', 'Minimal Wear', 'No', 2827),
('Butterfly Knife Gamma Doppler', 'Factory New', 'StatTrak', 2822),
('Butterfly Knife Gamma Doppler', 'Minimal Wear', 'StatTrak', 2862),

-- M9 Bayonet Gamma Doppler
('M9 Bayonet Gamma Doppler', 'Factory New', 'No', 1979),
('M9 Bayonet Gamma Doppler', 'Minimal Wear', 'No', 1838),
('M9 Bayonet Gamma Doppler', 'Factory New', 'StatTrak', 1797),
('M9 Bayonet Gamma Doppler', 'Minimal Wear', 'StatTrak', 1781),