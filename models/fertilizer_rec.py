import pandas as pd
import json
import os

class AdvancedFertilizerRecommender:
    def __init__(self):
        # Optimal soil values and classification ranges
        self.optimal_values = {
            'pH': 7.0,
            'EC': 1.0,
            'OC': 0.8,
            'N': 360,  # kg/ha
            'P': 16.25,  # kg/ha (using av_p)
            'K': 200,  # kg/ha (using av_k)
            'Zn': 0.9,  # ppm (using zinc)
            'Cu': 0.3,  # ppm (using cu)
            'Fe': 6.0,  # ppm (using iron)
            'Mn': 10.0,  # ppm (using mn)
            'S': 16.25  # ppm
        }

        # Complete crop requirements for all 27 crops (kg/ha)
        self.crop_requirements = {
            # Cereals
            'PADDY': {'N': 120, 'P': 60, 'K': 50, 'Zn': 5, 'Fe': 5, 'S': 20},
            'WHEAT': {'N': 120, 'P': 60, 'K': 40, 'Zn': 5, 'S': 20},
            'BAJRA': {'N': 80, 'P': 40, 'K': 40, 'Zn': 5},
            'MAIZE': {'N': 150, 'P': 75, 'K': 75, 'Zn': 5, 'S': 15},

            # Pulses
            'GRAM': {'N': 20, 'P': 60, 'K': 20, 'S': 15, 'Zn': 3},
            'MOONG': {'N': 20, 'P': 60, 'K': 20, 'S': 15},
            'SOYABEEN': {'N': 20, 'P': 80, 'K': 40, 'S': 20, 'Zn': 5},

            # Oilseeds
            'GROUNDNUT': {'N': 20, 'P': 60, 'K': 40, 'S': 20},
            'MUSTERD': {'N': 80, 'P': 40, 'K': 40, 'S': 40},

            # Commercial crops
            'SUGARCANE': {'N': 200, 'P': 80, 'K': 60, 'Zn': 5, 'Fe': 5, 'S': 20},
            'COTTON': {'N': 150, 'P': 75, 'K': 75, 'Zn': 5, 'S': 20},
            'CASTOR': {'N': 80, 'P': 40, 'K': 40, 'S': 20},

            # Vegetables
            'ONION': {'N': 150, 'P': 75, 'K': 100, 'S': 30},
            'POTATO': {'N': 180, 'P': 120, 'K': 150, 'Zn': 5, 'S': 30},
            'BRINJAL': {'N': 150, 'P': 75, 'K': 100, 'S': 20},
            'TOMATO': {'N': 150, 'P': 100, 'K': 120, 'S': 25},
            'CABBAGE': {'N': 180, 'P': 90, 'K': 120, 'S': 25},
            'CAULIFLOWER': {'N': 150, 'P': 100, 'K': 120, 'S': 25},
            'CARROT': {'N': 100, 'P': 80, 'K': 150, 'S': 20},
            'CUCUMBER': {'N': 100, 'P': 50, 'K': 100, 'S': 15},
            'BOTTLE GOURD': {'N': 100, 'P': 50, 'K': 100, 'S': 15},

            # Fruits
            'MANGO': {'N': 500, 'P': 250, 'K': 500, 'Zn': 5},
            'GUAVA': {'N': 500, 'P': 250, 'K': 500, 'Zn': 5},
            'AONLA': {'N': 500, 'P': 250, 'K': 500, 'Zn': 5},
            'KINOO': {'N': 500, 'P': 250, 'K': 500, 'Zn': 5},

            # Others
            'TURMERIC': {'N': 120, 'P': 60, 'K': 120, 'Zn': 5, 'S': 30},
            'GARLIC': {'N': 150, 'P': 75, 'K': 100, 'S': 30},
            'VEGETABLE': {'N': 150, 'P': 75, 'K': 100, 'S': 20}
        }

        # Enhanced fertilizer database with micronutrients
        self.fertilizers = {
            # Primary fertilizers
            'UREA': {'N': 46, 'P': 0, 'K': 0, 'S': 0},
            'DAP': {'N': 18, 'P': 46, 'K': 0, 'S': 0},
            'SSP': {'N': 0, 'P': 16, 'K': 0, 'S': 11},
            'MOP': {'N': 0, 'P': 0, 'K': 60, 'S': 0},
            'NPK': {'N': 12, 'P': 32, 'K': 16, 'S': 0},
            'NPS': {'N': 20, 'P': 20, 'K': 13, 'S': 16},
            'Ammonium Sulphate': {'N': 21, 'P': 0, 'K': 0, 'S': 24},

            # Micronutrient fertilizers
            'Zinc Sulphate': {'Zn': 21, 'S': 10},  # 21% Zn + 10% S
            'Ferrous Sulphate': {'Fe': 19, 'S': 10},  # 19% Fe + 10% S
            'Copper Sulphate': {'Cu': 25, 'S': 12},  # 25% Cu + 12% S
            'Manganese Sulphate': {'Mn': 32, 'S': 18},  # 32% Mn + 18% S

            # Organic options
            'Farmyard Manure': {'N': 0.5, 'P': 0.2, 'K': 0.5, 'micronutrients': 'trace'},
            'Vermicompost': {'N': 1.5, 'P': 0.5, 'K': 1.2, 'micronutrients': 'trace'}
        }

        # Bag sizes and units
        self.bag_sizes = {
            'UREA': 50,
            'DAP': 50,
            'SSP': 50,
            'MOP': 50,
            'NPK': 50,
            'NPS': 33.33,
            'Ammonium Sulphate': 50,
            'Zinc Sulphate': 5,
            'Ferrous Sulphate': 5,
            'Copper Sulphate': 5,
            'Manganese Sulphate': 5,
            'Farmyard Manure': 1000,  # 1 ton
            'Vermicompost': 1000     # 1 ton
        }

        # Crop-specific special considerations
        self.crop_special_notes = {
            'PADDY': "Requires more zinc in flooded conditions",
            'GROUNDNUT': "Needs sulphur for pod development",
            'SUGARCANE': "Split applications recommended (4-6 splits)",
            'POTATO': "Avoid excess nitrogen to prevent hollow heart",
            'FRUITS': "Foliar sprays recommended for micronutrients",
            'PULSES': "Rhizobium inoculation recommended for nitrogen fixation"
        }

        # Soil amendment recommendations
        self.soil_amendments = {
            'acidic': 'Lime (2-5 t/ha)',
            'alkaline': 'Gypsum (1-2 t/ha) + Organic matter',
            'saline': 'Gypsum (2-5 t/ha) + Leaching',
            'low_oc': '10-15 t/ha Farmyard manure or compost'
        }

    def classify_soil_parameters(self, soil_values):
        """Enhanced soil classification with more parameters"""
        classifications = {}

        # pH classification
        ph = soil_values.get('pH', 7.0)
        if ph < 4.0:
            classifications['pH'] = ('Extremely acidic', 'critical')
        elif 4.0 <= ph < 5.5:
            classifications['pH'] = ('Strongly acidic', 'critical')
        elif 5.5 <= ph < 6.0:
            classifications['pH'] = ('Medium acidic', 'moderate')
        elif 6.0 <= ph < 7.0:
            classifications['pH'] = ('Slightly acidic', 'optimal')
        elif ph == 7.0:
            classifications['pH'] = ('Neutral', 'ideal')
        elif 7.0 < ph <= 8.5:
            classifications['pH'] = ('Slightly saline', 'moderate')
        elif 8.5 < ph <= 9.3:
            classifications['pH'] = ('Tending to become alkaline', 'critical')
        else:
            classifications['pH'] = ('Alkaline', 'critical')

        # EC classification
        ec = soil_values.get('EC', 0.8)
        if ec < 1.0:
            classifications['EC'] = ('Normal', 'optimal')
        elif 1.0 <= ec < 2.0:
            classifications['EC'] = ('Critical for Germination', 'moderate')
        elif 2.0 <= ec < 3.0:
            classifications['EC'] = ('Critical for growth', 'critical')
        else:
            classifications['EC'] = ('Injurious', 'critical')

        # OC classification
        oc = soil_values.get('OC', 0.5)
        if oc < 0.5:
            classifications['OC'] = ('Low', 'critical')
        elif 0.5 <= oc < 0.8:
            classifications['OC'] = ('Medium', 'moderate')
        else:
            classifications['OC'] = ('High', 'optimal')

        # Enhanced nutrient classification with severity levels
        nutrient_ranges = {
            'N': [(0, 240, 'Low'), (240, 480, 'Medium'), (480, float('inf'), 'High')],
            'P': [(0, 10, 'Low'), (10, 22.5, 'Medium'), (22.5, float('inf'), 'High')],
            'K': [(0, 120, 'Low'), (120, 280, 'Medium'), (280, float('inf'), 'High')],
            'Zn': [(0, 0.6, 'Low'), (0.6, 1.2, 'Medium'), (1.2, float('inf'), 'High')],
            'Fe': [(0, 4, 'Low'), (4, 8, 'Medium'), (8, float('inf'), 'High')],
            'Cu': [(0, 0.2, 'Low'), (0.2, 0.4, 'Medium'), (0.4, float('inf'), 'High')],
            'S': [(0, 10, 'Low'), (10, 22.5, 'Medium'), (22.5, float('inf'), 'High')],
            'Mn': [(0, 5, 'Low'), (5, 15, 'Medium'), (15, float('inf'), 'High')]
        }

        # Map input parameter names to standard names
        param_mapping = {
            'av_p': 'P',
            'av_k': 'K',
            'zinc': 'Zn',
            'cu': 'Cu',
            'iron': 'Fe',
            'mn': 'Mn'
        }

        for param, ranges in nutrient_ranges.items():
            # Check both standard name and input name
            input_param = None
            for k, v in param_mapping.items():
                if v == param:
                    input_param = k
                    break
            
            value = None
            if param in soil_values:
                value = soil_values[param]
            elif input_param and input_param in soil_values:
                value = soil_values[input_param]
            
            if value is not None:
                for min_val, max_val, category in ranges:
                    if min_val <= value < max_val:
                        severity = 'critical' if category == 'Low' else 'moderate' if category == 'Medium' else 'optimal'
                        classifications[param] = (category, severity)
                        break

        return classifications

    def calculate_deficiencies(self, soil_values, crop):
        """Enhanced deficiency calculation with crop growth stages"""
        deficiencies = {}
        crop_req = self.crop_requirements.get(crop.upper(), {})

        # Get crop growth stage multipliers
        growth_stage_multipliers = self.get_growth_stage_multipliers(crop)

        # Map input parameter names to standard names
        param_mapping = {
            'av_p': 'P',
            'av_k': 'K',
            'zinc': 'Zn',
            'cu': 'Cu',
            'iron': 'Fe',
            'mn': 'Mn'
        }

        for nutrient, optimal in self.optimal_values.items():
            # Skip pH and EC (handled separately)
            if nutrient in ['pH', 'EC', 'OC']:
                continue
                
            # Get the correct parameter name
            input_param = None
            for k, v in param_mapping.items():
                if v == nutrient:
                    input_param = k
                    break
            
            # Get the soil value
            soil_value = None
            if nutrient in soil_values:
                soil_value = soil_values[nutrient]
            elif input_param and input_param in soil_values:
                soil_value = soil_values[input_param]
            else:
                continue

            # Calculate target based on crop requirement and optimal value
            crop_need = crop_req.get(nutrient, 0)
            target = max(optimal, optimal * 0.5 + crop_need * 0.5)  # Weighted average

            # Adjust for growth stage
            target *= growth_stage_multipliers.get(nutrient, 1.0)

            if soil_value < target:
                deficiencies[nutrient] = {
                    'deficiency': target - soil_value,
                    'severity': 'critical' if (target - soil_value) > target*0.5 else 'moderate'
                }
            else:
                deficiencies[nutrient] = {
                    'deficiency': 0,
                    'severity': 'optimal'
                }

        return deficiencies

    def get_growth_stage_multipliers(self, crop):
        """Returns nutrient needs at different growth stages"""
        # Default multipliers (vegetative, flowering, fruiting stages)
        multipliers = {
            'N': [1.2, 1.0, 0.8],  # More N needed in vegetative stage
            'P': [0.8, 1.5, 1.2],   # More P needed during flowering
            'K': [1.0, 1.2, 1.5],    # More K needed during fruiting
            'micronutrients': [1.0, 1.2, 1.0]
        }

        # Crop-specific adjustments
        if crop.upper() in ['PADDY', 'WHEAT', 'BAJRA']:
            multipliers['N'][1] = 1.2  # Cereals need more N during tillering
        elif crop.upper() in ['GROUNDNUT', 'SOYABEEN']:
            multipliers['P'][1] = 1.8  # Pulses need more P during flowering
        elif crop.upper() in ['SUGARCANE']:
            multipliers['N'] = [1.5, 1.5, 1.0]  # Sugarcane needs continuous N

        return {
            'N': max(multipliers['N']),
            'P': max(multipliers['P']),
            'K': max(multipliers['K']),
            'Zn': multipliers['micronutrients'][1],
            'Fe': multipliers['micronutrients'][1],
            'Cu': multipliers['micronutrients'][1],
            'Mn': multipliers['micronutrients'][1],
            'S': multipliers['micronutrients'][1]
        }

    def recommend_fertilizers(self, deficiencies, crop):
        """Enhanced fertilizer recommendation with multiple strategies"""
        recommendations = []
        remaining_deficiencies = deficiencies.copy()

        # Step 1: Recommend soil amendments based on pH/EC/OC
        amendments = self.recommend_soil_amendments(remaining_deficiencies)
        if amendments:
            recommendations.extend(amendments)

        # Step 2: Use complex fertilizers to address multiple deficiencies
        complex_fert_rec = self.recommend_complex_fertilizers(remaining_deficiencies, crop)
        if complex_fert_rec:
            recommendations.extend(complex_fert_rec['recommendations'])
            remaining_deficiencies = complex_fert_rec['remaining_def']

        # Step 3: Address remaining deficiencies with straight fertilizers
        straight_fert_rec = self.recommend_straight_fertilizers(remaining_deficiencies)
        if straight_fert_rec:
            recommendations.extend(straight_fert_rec)

        # Step 4: Add organic recommendations based on OC level
        organic_rec = self.recommend_organic_manures(deficiencies)
        if organic_rec:
            recommendations.extend(organic_rec)

        # Step 5: Add special crop-specific recommendations
        special_rec = self.recommend_special_crop_needs(crop, deficiencies)
        if special_rec:
            recommendations.extend(special_rec)

        return recommendations

    def recommend_soil_amendments(self, deficiencies):
        """Recommend lime/gypsum/organic matter based on soil conditions"""
        amendments = []
        ph_status = deficiencies.get('pH', {}).get('classification', ('Neutral', 'optimal'))[1]
        ec_status = deficiencies.get('EC', {}).get('classification', ('Normal', 'optimal'))[1]
        oc_status = deficiencies.get('OC', {}).get('classification', ('Medium', 'moderate'))[1]

        if ph_status == 'critical':
            ph_val = deficiencies['pH']['value']
            if ph_val < 5.5:
                amendments.append({
                    'type': 'Soil Amendment',
                    'name': 'Lime',
                    'amount': '2-5 t/ha',
                    'purpose': 'Raise pH to optimal level',
                    'time': 'Apply 2-3 weeks before planting and mix well'
                })
            elif ph_val > 8.5:
                amendments.append({
                    'type': 'Soil Amendment',
                    'name': 'Gypsum + Organic Matter',
                    'amount': '1-2 t/ha gypsum + 10 t/ha FYM',
                    'purpose': 'Lower pH and improve soil structure',
                    'time': 'Apply during land preparation'
                })

        if ec_status == 'critical':
            amendments.append({
                'type': 'Soil Amendment',
                'name': 'Gypsum + Leaching',
                'amount': '2-5 t/ha gypsum + 10-15 cm standing water',
                'purpose': 'Reduce soil salinity',
                'time': 'Apply gypsum before leaching irrigation'
            })

        if oc_status == 'critical':
            amendments.append({
                'type': 'Soil Amendment',
                'name': 'Organic Matter',
                'amount': '10-15 t/ha FYM or compost',
                'purpose': 'Improve soil organic carbon',
                'time': 'Apply during land preparation'
            })

        return amendments

    def recommend_complex_fertilizers(self, deficiencies, crop):
        """Smart recommendation of complex fertilizers"""
        remaining_def = deficiencies.copy()
        recommendations = []

        # Strategy 1: Prefer NPS for crops needing sulphur
        if crop.upper() in ['OILSEEDS', 'PULSES', 'GROUNDNUT', 'MUSTERD']:
            if remaining_def.get('N', {}).get('deficiency', 0) > 0 and \
               remaining_def.get('P', {}).get('deficiency', 0) > 0 and \
               remaining_def.get('S', {}).get('deficiency', 0) > 0:
                amount = min(
                    remaining_def['N']['deficiency'] / (self.fertilizers['NPS']['N']/100),
                    remaining_def['P']['deficiency'] / (self.fertilizers['NPS']['P']/100),
                    remaining_def['S']['deficiency'] / (self.fertilizers['NPS']['S']/100)
                )
                if amount > 0:
                    rec = {
                        'fertilizer': 'NPS',
                        'amount_kg': amount,
                        'bags': amount / self.bag_sizes['NPS'],
                        'covers': {
                            'N': amount * self.fertilizers['NPS']['N']/100,
                            'P': amount * self.fertilizers['NPS']['P']/100,
                            'S': amount * self.fertilizers['NPS']['S']/100
                        }
                    }
                    recommendations.append(rec)
                    # Update remaining deficiencies
                    remaining_def['N']['deficiency'] -= rec['covers']['N']
                    remaining_def['P']['deficiency'] -= rec['covers']['P']
                    remaining_def['S']['deficiency'] -= rec['covers']['S']

        # Strategy 2: Use DAP for high P requiring crops
        if crop.upper() in ['POTATO', 'TOMATO', 'FRUITS']:
            if remaining_def.get('N', {}).get('deficiency', 0) > 0 and \
               remaining_def.get('P', {}).get('deficiency', 0) > 0:
                amount = min(
                    remaining_def['N']['deficiency'] / (self.fertilizers['DAP']['N']/100),
                    remaining_def['P']['deficiency'] / (self.fertilizers['DAP']['P']/100)
                )
                if amount > 0:
                    rec = {
                        'fertilizer': 'DAP',
                        'amount_kg': amount,
                        'bags': amount / self.bag_sizes['DAP'],
                        'covers': {
                            'N': amount * self.fertilizers['DAP']['N']/100,
                            'P': amount * self.fertilizers['DAP']['P']/100
                        }
                    }
                    recommendations.append(rec)
                    remaining_def['N']['deficiency'] -= rec['covers']['N']
                    remaining_def['P']['deficiency'] -= rec['covers']['P']

        # Strategy 3: Use NPK for balanced nutrition
        if remaining_def.get('N', {}).get('deficiency', 0) > 0 and \
           remaining_def.get('P', {}).get('deficiency', 0) > 0 and \
           remaining_def.get('K', {}).get('deficiency', 0) > 0:
            amount = min(
                remaining_def['N']['deficiency'] / (self.fertilizers['NPK']['N']/100),
                remaining_def['P']['deficiency'] / (self.fertilizers['NPK']['P']/100),
                remaining_def['K']['deficiency'] / (self.fertilizers['NPK']['K']/100)
            )
            if amount > 0:
                rec = {
                    'fertilizer': 'NPK',
                    'amount_kg': amount,
                    'bags': amount / self.bag_sizes['NPK'],
                    'covers': {
                        'N': amount * self.fertilizers['NPK']['N']/100,
                        'P': amount * self.fertilizers['NPK']['P']/100,
                        'K': amount * self.fertilizers['NPK']['K']/100
                    }
                }
                recommendations.append(rec)
                remaining_def['N']['deficiency'] -= rec['covers']['N']
                remaining_def['P']['deficiency'] -= rec['covers']['P']
                remaining_def['K']['deficiency'] -= rec['covers']['K']

        return {
            'recommendations': recommendations,
            'remaining_def': remaining_def
        }

    def recommend_straight_fertilizers(self, deficiencies):
        """Recommend straight fertilizers for remaining deficiencies"""
        recommendations = []

        for nutrient, data in deficiencies.items():
            deficiency = data.get('deficiency', 0)
            if deficiency <= 0:
                continue

            fert_map = {
                'N': 'UREA',
                'P': 'SSP',
                'K': 'MOP',
                'S': 'Ammonium Sulphate',
                'Zn': 'Zinc Sulphate',
                'Fe': 'Ferrous Sulphate',
                'Cu': 'Copper Sulphate',
                'Mn': 'Manganese Sulphate'
            }

            if nutrient in fert_map:
                fert = fert_map[nutrient]
                percent = self.fertilizers[fert].get(nutrient, 0)
                if percent > 0:
                    amount = (deficiency * 100) / percent
                    rec = {
                        'fertilizer': fert,
                        'amount_kg': amount,
                        'bags': amount / self.bag_sizes.get(fert, 1),
                        'covers': {nutrient: deficiency}
                    }
                    if fert in ['Zinc Sulphate', 'Ferrous Sulphate', 'Copper Sulphate',
                               'Manganese Sulphate']:
                        rec['unit'] = 'Pkt' if amount < 50 else 'Bags'
                    recommendations.append(rec)

        return recommendations

    def recommend_organic_manures(self, deficiencies):
        """Recommend organic manures based on OC level and deficiencies"""
        recommendations = []
        oc_status = deficiencies.get('OC', {}).get('classification', ('Medium', 'moderate'))[1]

        if oc_status == 'critical':
            recommendations.append({
                'fertilizer': 'Farmyard Manure',
                'amount_kg': 10000,  # 10 t/ha
                'bags': 10,
                'unit': 'Tons',
                'purpose': 'Improve soil organic matter and micronutrients',
                'application': 'Spread evenly and mix during land preparation'
            })
        elif any(def_val.get('deficiency', 0) > 0 for def_val in deficiencies.values()):
            recommendations.append({
                'fertilizer': 'Vermicompost',
                'amount_kg': 5000,  # 5 t/ha
                'bags': 5,
                'unit': 'Tons',
                'purpose': 'Provide slow-release nutrients and improve soil health',
                'application': 'Apply in planting pits or as top dressing'
            })

        return recommendations

    def recommend_special_crop_needs(self, crop, deficiencies):
        """Special recommendations for specific crops"""
        recommendations = []
        crop_upper = crop.upper()

        # Rice needs zinc in deficient soils
        if crop_upper == 'PADDY' and deficiencies.get('Zn', {}).get('deficiency', 0) > 0:
            recommendations.append({
                'fertilizer': 'Zinc Sulphate',
                'amount_kg': 25,  # 25 kg/ha
                'bags': 5,
                'unit': 'Pkt (5 kg)',
                'purpose': 'Prevent khaira disease in paddy',
                'application': 'Apply as basal dose or foliar spray (0.5%)'
            })

        # Pulses need rhizobium inoculation
        if crop_upper in ['GRAM', 'MOONG', 'SOYABEEN']:
            recommendations.append({
                'fertilizer': 'Rhizobium Culture',
                'amount_kg': 1,  # 1 kg/ha
                'bags': 1,
                'unit': 'Packet',
                'purpose': 'Enhance nitrogen fixation',
                'application': 'Mix with seeds before sowing'
            })

        # Fruits need foliar sprays
        if crop_upper in ['MANGO', 'GUAVA', 'AONLA', 'KINOO']:
            if any(def_val.get('deficiency', 0) > 0 for nutrient, def_val in deficiencies.items()
                  if nutrient in ['Zn', 'Fe', 'Cu', 'Mn']):
                recommendations.append({
                    'fertilizer': 'Micronutrient Mixture',
                    'amount_kg': 5,  # 5 kg/ha
                    'bags': 1,
                    'unit': 'Packet',
                    'purpose': 'Correct micronutrient deficiencies',
                    'application': 'Foliar spray (0.5%) at 15 day intervals'
                })

        return recommendations

    def generate_report(self, soil_values, crop, farmer_name=None, location=None):
        """Generate comprehensive fertilizer recommendation report"""
        # Classify soil parameters
        classifications = self.classify_soil_parameters(soil_values)

        # Calculate deficiencies
        deficiencies = self.calculate_deficiencies(soil_values, crop)

        # Get fertilizer recommendations
        recommendations = self.recommend_fertilizers(deficiencies, crop)

        # Create report
        report = f"\n{'='*80}\nFERTILIZER RECOMMENDATION REPORT\n{'='*80}\n"

        # Header information
        if farmer_name:
            report += f"Farmer Name: {farmer_name}\n"
        if location:
            report += f"Location: {location}\n"
        report += f"Crop: {crop.upper()}\n"
        report += f"Recommendation Date: {pd.Timestamp.now().strftime('%d-%b-%Y')}\n"
        report += f"\n{'='*80}\n"

        # Soil test results
        report += "\nSOIL TEST RESULTS:\n"
        soil_table = []
        
        # Map input parameter names to display names
        display_names = {
            'pH': 'pH',
            'EC': 'EC (dS/m)',
            'OC': 'OC (%)',
            'N': 'Nitrogen (kg/ha)',
            'av_p': 'Available P (kg/ha)',
            'av_k': 'Available K (kg/ha)',
            'S': 'Sulphur (ppm)',
            'zinc': 'Zinc (ppm)',
            'cu': 'Copper (ppm)',
            'iron': 'Iron (ppm)',
            'mn': 'Manganese (ppm)'
        }
        
        for param, value in soil_values.items():
            display_name = display_names.get(param, param)
            if param in classifications:
                category, severity = classifications[param]
                soil_table.append({
                    'Parameter': display_name,
                    'Value': value,
                    'Classification': category,
                    'Status': severity.upper()
                })
            else:
                # For parameters without classification (like micronutrients)
                soil_table.append({
                    'Parameter': display_name,
                    'Value': value,
                    'Classification': 'N/A',
                    'Status': 'N/A'
                })

        df_soil = pd.DataFrame(soil_table)
        report += df_soil.to_string(index=False)
        report += f"\n\n{'='*80}\n"

        # Deficiency analysis
        report += "\nNUTRIENT DEFICIENCY ANALYSIS:\n"
        def_table = []
        for nutrient, data in deficiencies.items():
            if nutrient not in ['pH', 'EC', 'OC']:
                def_table.append({
                    'Nutrient': nutrient,
                    'Deficiency (kg/ha)': f"{data.get('deficiency', 0):.2f}",
                    'Severity': data.get('severity', 'optimal').upper(),
                    'Impact': 'Critical' if data.get('deficiency', 0) > 0 else 'Adequate'
                })

        df_def = pd.DataFrame(def_table)
        report += df_def.to_string(index=False)
        report += f"\n\n{'='*80}\n"

        # Fertilizer recommendations
        report += "\nFERTILIZER RECOMMENDATIONS:\n"
        fert_table = []
        for rec in recommendations:
            if rec.get('type') == 'Soil Amendment':
                fert_table.append({
                    'Type': 'Soil Amendment',
                    'Product': rec['name'],
                    'Dose': rec['amount'],
                    'Purpose': rec['purpose'],
                    'Application': rec.get('application', 'During land preparation')
                })
            else:
                unit = rec.get('unit', 'Bags')
                fert_table.append({
                    'Type': 'Fertilizer',
                    'Product': rec['fertilizer'],
                    'Dose (kg/ha)': f"{rec['amount_kg']:.2f}",
                    'Quantity': f"{rec['bags']:.2f} {unit}",
                    'Covers': ', '.join([f"{k}: {v:.2f} kg/ha" for k, v in rec.get('covers', {}).items()])
                })

        df_fert = pd.DataFrame(fert_table)
        report += df_fert.to_string(index=False)
        report += f"\n\n{'='*80}\n"

        # Special notes
        report += "\nSPECIAL RECOMMENDATIONS:\n"
        crop_upper = crop.upper()

        # Soil amendment notes
        ph_status = classifications.get('pH', ('Neutral', 'optimal'))[1]
        if ph_status == 'critical':
            report += "- Soil pH needs correction before fertilizer application\n"

        # Crop-specific notes
        if crop_upper in self.crop_special_notes:
            report += f"- {self.crop_special_notes[crop_upper]}\n"

        # Application method notes
        if crop_upper in ['SUGARCANE', 'POTATO', 'COTTON']:
            report += "- Split applications recommended (3-4 splits during crop growth)\n"
        elif crop_upper in ['PADDY', 'WHEAT']:
            report += "- Basal application at planting and top dressing recommended\n"
        elif crop_upper in ['FRUITS', 'MANGO', 'GUAVA']:
            report += "- Soil application + foliar sprays recommended for better nutrient uptake\n"

        # Organic farming note
        if soil_values.get('OC', 0) < 0.5:
            report += "- Regular organic matter addition recommended to improve soil health\n"

        report += f"\n{'='*80}\n"

        return report

    def generate_report_json(self, soil_values, crop, farmer_name=None, location=None):
        """Generate comprehensive fertilizer recommendation report in JSON format"""
        # Classify soil parameters
        classifications = self.classify_soil_parameters(soil_values)

        # Calculate deficiencies
        deficiencies = self.calculate_deficiencies(soil_values, crop)

        # Get fertilizer recommendations
        recommendations = self.recommend_fertilizers(deficiencies, crop)
        
        # Current date
        current_date = pd.Timestamp.now().strftime('%d-%b-%Y')

        # Create JSON report structure
        report_data = {
            "header": {
                "title": "FERTILIZER RECOMMENDATION REPORT",
                "farmer_name": farmer_name,
                "location": location,
                "crop": crop.upper(),
                "date": current_date
            },
            "soil_test_results": [],
            "deficiency_analysis": [],
            "fertilizer_recommendations": [],
            "special_recommendations": []
        }

        # Soil test results
        display_names = {
            'pH': 'pH',
            'EC': 'EC (dS/m)',
            'OC': 'OC (%)',
            'N': 'Nitrogen (kg/ha)',
            'P': 'Phosphorus (kg/ha)',
            'K': 'Potassium (kg/ha)',
            'S': 'Sulphur (ppm)',
            'Zn': 'Zinc (ppm)',
            'Cu': 'Copper (ppm)',
            'Fe': 'Iron (ppm)',
            'Mn': 'Manganese (ppm)'
        }
        
        for param, value in soil_values.items():
            display_name = display_names.get(param, param)
            soil_result = {
                "parameter": display_name,
                "value": value,
                "classification": "N/A",
                "status": "N/A"
            }
            
            if param in classifications:
                category, severity = classifications[param]
                soil_result["classification"] = category
                soil_result["status"] = severity.upper()
                
            report_data["soil_test_results"].append(soil_result)

        # Deficiency analysis
        for nutrient, data in deficiencies.items():
            if nutrient not in ['pH', 'EC', 'OC']:
                deficiency_data = {
                    "nutrient": nutrient,
                    "deficiency": round(data.get('deficiency', 0), 2),
                    "severity": data.get('severity', 'optimal').upper(),
                    "impact": 'Critical' if data.get('deficiency', 0) > 0 else 'Adequate'
                }
                report_data["deficiency_analysis"].append(deficiency_data)

        # Fertilizer recommendations
        for rec in recommendations:
            if rec.get('type') == 'Soil Amendment':
                fert_data = {
                    "type": "Soil Amendment",
                    "product": rec['name'],
                    "dose": rec['amount'],
                    "purpose": rec['purpose'],
                    "application": rec.get('application', 'During land preparation')
                }
            else:
                unit = rec.get('unit', 'Bags')
                fert_data = {
                    "type": "Fertilizer",
                    "product": rec['fertilizer'],
                    "dose_kg_ha": round(rec['amount_kg'], 2),
                    "quantity": f"{round(rec['bags'], 2)} {unit}",
                    "covers": {k: round(v, 2) for k, v in rec.get('covers', {}).items()}
                }
            report_data["fertilizer_recommendations"].append(fert_data)

        # Special recommendations
        crop_upper = crop.upper()
        
        # Soil amendment notes
        ph_status = classifications.get('pH', ('Neutral', 'optimal'))[1]
        if ph_status == 'critical':
            report_data["special_recommendations"].append(
                "Soil pH needs correction before fertilizer application"
            )

        # Crop-specific notes
        if crop_upper in self.crop_special_notes:
            report_data["special_recommendations"].append(
                self.crop_special_notes[crop_upper]
            )

        # Application method notes
        if crop_upper in ['SUGARCANE', 'POTATO', 'COTTON']:
            report_data["special_recommendations"].append(
                "Split applications recommended (3-4 splits during crop growth)"
            )
        elif crop_upper in ['PADDY', 'WHEAT']:
            report_data["special_recommendations"].append(
                "Basal application at planting and top dressing recommended"
            )
        elif crop_upper in ['FRUITS', 'MANGO', 'GUAVA']:
            report_data["special_recommendations"].append(
                "Soil application + foliar sprays recommended for better nutrient uptake"
            )

        # Organic farming note
        if soil_values.get('OC', 0) < 0.5:
            report_data["special_recommendations"].append(
                "Regular organic matter addition recommended to improve soil health"
            )

        return report_data

# Example usage
if __name__ == "__main__":
    # Create recommender instance
    recommender = AdvancedFertilizerRecommender()

    # Example soil test values with the specified parameters
    soil_test = {
        'pH': 4.4,
        'EC': 0.79,
        'OC': 1.780,
        'N': 250,
        'P': 15,
        'K': 150,
        'Zn': 6.5,
        'Cu': 0.1,
        'Fe': 1.11,
        'Mn': 45.270,
        'S': 20,
    }

    # Generate and print report
    report = recommender.generate_report(
        soil_values=soil_test,
        crop="Wheat",
        farmer_name="Ramesh Kumar",
        location="Village XYZ, District ABC",
    )
    print(report)
     # Load the database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(current_dir, '..', 'data', 'database.json')
    with open(database_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Function to retrieve data for a given crop name
    def get_crop_data(crop_name):
        # Normalize the key for case-insensitive match
        crop_key = next((key for key in data if key.lower() == crop_name.lower()), None)

        if crop_key:
            crop_data = data[crop_key]
            print(f"\n🔍 Data for '{crop_key}':\n")
            print(json.dumps(crop_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Crop '{crop_name}' not found in the database.")
    crop_name = "wheat"
    get_crop_data(crop_name)
