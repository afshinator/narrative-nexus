import json

# Content from web_extract results - exact markdown returned by the tool
# I'll estimate char counts from what I can see in the tool output

# For web_extract: pages >5000 chars are LLM-summarized to ~5000 chars
# All content below is the actual returned markdown

contents = {
    "NPR Vzla 2": """# A Week After Venezuela's Devastating Double Earthquakes: Key Developments

**Source:** NPR, July 1, 2026  
**Original Title:** Untold casualties and humanitarian needs: What to know a week from Venezuela's quakes  
**Author:** Fatima Al-Kassab  
**Contributors:** Eyder Peralta, John Otis, Fernando Narro, María Graterol, Sergio Martínez-Beltrán, Fatma Tanis, Manuel Rueda

---

## 1. Key Excerpts (Quotes & Critical Data)

> **U.N. Humanitarian Coordinator in Venezuela Gianluca Rampolla**  
> "The death toll will unavoidably and sadly keep on growing as the search-and-rescue operation continues, and as we are able to detail further assessment of the impacts of the quakes."  
> "The heroism of the people and the solidarity is outstanding, and this somehow mitigates, a little bit obviously, the pain and the needs of the people affected on the ground."

> **Resident Rosalia Bustamante** on government delays costing lives:  
> "There were people in the ruins responding when we called out to them. But now, they are dead."

> **Construction worker Julio Meléndez** on bureaucratic obstacles:  
> "The only thing the authorities do is get in the way."

> **Displaced resident Mirna Castillo**  
> "How are we going to live in a place that's about to crack open? … It's just one chaos after another."

> **Alonso Guanipa Toyo**, brother of missing deportee Víctor (32):  
> "The government is not doing anything. My family is looking for him in the hospitals, in the shelters, in the morgues."

> **César Jiménez**, Project Hope Venezuela:  
> "We are doing our best as Venezuelans to support our people. This is a unique moment in our history. Nobody saw this coming, and we need a lot of support."

> **Satellite data analysis** (Corey Scher & Jamon Van Den Hoek, Oregon State University):  
> Estimated **58,870 buildings** likely damaged or destroyed.

> **U.N. International Organization for Migration**:  
> Up to **6.8 million people** could be affected.

> **Official toll** (National Assembly President Jorge Rodríguez, as of Wednesday):  
> **2,295 dead**, **11,200+ injured**, **tens of thousands** still unaccounted for.

> **Interim President Delcy Rodríguez** after rescue of 3-year-old Klieber Morán:  
> "A source of hope for our people."

---

## 2. Comprehensive Summary

### The Earthquakes
- **Date & time:** June 24, 2026, at 6:04 p.m. local time.
- **Magnitudes:** **7.2 and 7.5**, occurring within seconds of each other.
- **Epicenters:** Yaracuy state, west of Caracas.
- **Hardest‑hit area:** La Guaira state (coastal).
- Worst earthquake disaster in Venezuela in over a century.

### Human Toll & Damage
- **Deaths (official):** 2,295 (as of July 1).
- **Injured:** More than 11,200.
- **Missing:** Tens of thousands.
- U.N. procured **10,000 body bags** – Rampolla expressed hope the actual need would be smaller.
- Satellite analysis: ~58,870 buildings damaged/destroyed.
- Up to **6.8 million people** may need shelter, water, sanitation, healthcare, and relief.

### Government Response & Criticism
- Widespread public anger over slow, inadequate reaction.
- Residents dig through rubble with bare hands; bodies placed in garbage bags/plastic sheets.
- Police, army slow to arrive; set up roadblocks demanding **government permits** even from doctors/rescue workers.
- Example: Julio Meléndez delayed two days trying to bring a jackhammer, required to show permit and sales receipt.
- Government promises large camps, new homes "in a very short time," and a commission to assess housing/infrastructure.
- Healthcare system at breaking point – already underfunded for years; hospitals overwhelmed, damaged, health workers exhausted.

### Notable Rescues & Lost Lives
- **Miraculous rescue:** 3‑year‑old Klieber Morán pulled alive from rubble in La Guaira **six days** after the quakes.
- **Tragic story:** Venezuelan deportees from the U.S. killed when their processing hotel collapsed hours after arrival. Flight carried **146 deportees**; unclear if any survived. Víctor Guanipa Toyo (32) among the missing; family searching hospitals, shelters, morgues.

### Humanitarian Crisis
- Thousands living on sidewalks, parks, soccer fields; fear of returning to damaged buildings.
- Hospitals overwhelmed, some beyond capacity.
- Warnings of infectious disease spread; hospitals damaged, doctors missing.
- Karol Bassim (International Medical Corps): majority of people in hardest-hit areas "without food, drinking water, shelter or access to basic healthcare."

### International Support
- **United States:** Search & rescue teams, military assets, **$150 million** to charities/U.N. agencies – described as one of the strongest U.S. responses since USAID dismantlement.
- **European Union:** Over **$5 million** in humanitarian aid; hundreds of responders; Copernicus satellite imagery service activated.
- **United Kingdom:** Specialist search & rescue teams, over **$2 million** in funding.
- **Other countries:** Brazil, Chile, China, India, Japan, Turkey, etc.""",
}

# Let me just print the lengths of the actual content returned by web_extract
print(f"NPR Vzla 2 content length: {len(contents['NPR Vzla 2'])}")
