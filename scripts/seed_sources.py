from app.database import get_supabase

def seed_sources():
    supabase = get_supabase()

    sources = [
        {"state": "Alabama", "state_abbreviation": "AL", "url": "https://purchasing.alabama.gov"},
        {"state": "Alaska", "state_abbreviation": "AK", "url": "https://doa.alaska.gov/dgs"},
        {"state": "Arizona", "state_abbreviation": "AZ", "url": "https://spo.az.gov"},
        {"state": "Arkansas", "state_abbreviation": "AR", "url": "https://www.dfa.arkansas.gov/office/state-procurement"},
        {"state": "California", "state_abbreviation": "CA", "url": "https://www.dgs.ca.gov/PD"},
        {"state": "Colorado", "state_abbreviation": "CO", "url": "https://www.colorado.gov/osc/procurement"},
        {"state": "Connecticut", "state_abbreviation": "CT", "url": "https://portal.ct.gov/DAS/Procurement"},
        {"state": "Delaware", "state_abbreviation": "DE", "url": "https://mymarketplace.delaware.gov"},
        {"state": "Florida", "state_abbreviation": "FL", "url": "https://www.dms.myflorida.com/business_operations/state_purchasing"},
        {"state": "Georgia", "state_abbreviation": "GA", "url": "https://doas.ga.gov/state-purchasing"},
        {"state": "Hawaii", "state_abbreviation": "HI", "url": "https://spo.hawaii.gov"},
        {"state": "Idaho", "state_abbreviation": "ID", "url": "https://purchasing.idaho.gov"},
        {"state": "Illinois", "state_abbreviation": "IL", "url": "https://www2.illinois.gov/cpo"},
        {"state": "Indiana", "state_abbreviation": "IN", "url": "https://www.in.gov/idoa/procurement"},
        {"state": "Iowa", "state_abbreviation": "IA", "url": "https://das.iowa.gov/procurement"},
        {"state": "Kansas", "state_abbreviation": "KS", "url": "https://admin.ks.gov/offices/procurement-contracts"},
        {"state": "Kentucky", "state_abbreviation": "KY", "url": "https://finance.ky.gov/services/eprocurement"},
        {"state": "Louisiana", "state_abbreviation": "LA", "url": "https://www.doa.la.gov/doa/osp"},
        {"state": "Maine", "state_abbreviation": "ME", "url": "https://www.maine.gov/dafs/bbm/procurementservices"},
        {"state": "Maryland", "state_abbreviation": "MD", "url": "https://procurement.maryland.gov"},
        {"state": "Massachusetts", "state_abbreviation": "MA", "url": "https://www.mass.gov/orgs/operational-services-division"},
        {"state": "Michigan", "state_abbreviation": "MI", "url": "https://www.michigan.gov/dtmb/procurement"},
        {"state": "Minnesota", "state_abbreviation": "MN", "url": "https://mn.gov/admin/government/procurement"},
        {"state": "Mississippi", "state_abbreviation": "MS", "url": "https://www.dfa.ms.gov/dfa-offices/purchasing-travel"},
        {"state": "Missouri", "state_abbreviation": "MO", "url": "https://oa.mo.gov/purchasing"},
        {"state": "Montana", "state_abbreviation": "MT", "url": "https://spb.mt.gov"},
        {"state": "Nebraska", "state_abbreviation": "NE", "url": "https://das.nebraska.gov/materiel/purchasing.html"},
        {"state": "Nevada", "state_abbreviation": "NV", "url": "https://purchasing.nv.gov"},
        {"state": "New Hampshire", "state_abbreviation": "NH", "url": "https://www.das.nh.gov/purchasing"},
        {"state": "New Jersey", "state_abbreviation": "NJ", "url": "https://www.state.nj.us/treasury/purchase"},
        {"state": "New Mexico", "state_abbreviation": "NM", "url": "https://www.generalservices.state.nm.us/state-purchasing"},
        {"state": "New York", "state_abbreviation": "NY", "url": "https://ogs.ny.gov/procurement"},
        {"state": "North Carolina", "state_abbreviation": "NC", "url": "https://ncadmin.nc.gov/government/procurement"},
        {"state": "North Dakota", "state_abbreviation": "ND", "url": "https://www.omb.nd.gov/doing-business-state/procurement"},
        {"state": "Ohio", "state_abbreviation": "OH", "url": "https://procure.ohio.gov"},
        {"state": "Oklahoma", "state_abbreviation": "OK", "url": "https://omes.ok.gov/services/purchasing"},
        {"state": "Oregon", "state_abbreviation": "OR", "url": "https://www.oregon.gov/das/procurement"},
        {"state": "Pennsylvania", "state_abbreviation": "PA", "url": "https://www.dgs.pa.gov/Materials-Services-Procurement"},
        {"state": "Rhode Island", "state_abbreviation": "RI", "url": "https://purchasing.ri.gov"},
        {"state": "South Carolina", "state_abbreviation": "SC", "url": "https://procurement.sc.gov"},
        {"state": "South Dakota", "state_abbreviation": "SD", "url": "https://boa.sd.gov/central-services/procurement-management"},
        {"state": "Tennessee", "state_abbreviation": "TN", "url": "https://www.tn.gov/generalservices/procurement"},
        {"state": "Texas", "state_abbreviation": "TX", "url": "https://comptroller.texas.gov/purchasing"},
        {"state": "Utah", "state_abbreviation": "UT", "url": "https://purchasing.utah.gov"},
        {"state": "Vermont", "state_abbreviation": "VT", "url": "https://bgs.vermont.gov/purchasing"},
        {"state": "Virginia", "state_abbreviation": "VA", "url": "https://eva.virginia.gov"},
        {"state": "Washington", "state_abbreviation": "WA", "url": "https://des.wa.gov/services/contracting-purchasing"},
        {"state": "West Virginia", "state_abbreviation": "WV", "url": "https://purchasing.wv.gov"},
        {"state": "Wisconsin", "state_abbreviation": "WI", "url": "https://vendornet.wi.gov"},
        {"state": "Wyoming", "state_abbreviation": "WY", "url": "https://ai.wyo.gov/divisions/procurement-services"},
    ]

    for source in sources:
        supabase.table("sources").upsert(source, on_conflict="url").execute()

    print(f"Seeded {len(sources)} sources")

if __name__ == "__main__":
    seed_sources()
