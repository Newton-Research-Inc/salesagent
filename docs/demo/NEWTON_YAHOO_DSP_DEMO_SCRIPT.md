# Newton + Yahoo DSP Demo Script
## Agency CTV Workflow - Prisma Integration

This demo shows Newton executing the real agency CTV buying workflow:
1. **Prisma** is the source of truth for campaign planning
2. **Publishers** send deal IDs via email
3. **Newton** registers deals and creatives in Yahoo DSP
4. **Newton** activates the campaign

---

## 🎯 Overview

### The Agency's Real Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     AGENCY CTV WORKFLOW                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. PRISMA PLANNING (Source of Truth)                                   │
│     └─ Campaign details, placements, budgets, naming conventions        │
│                                                                          │
│  2. PUBLISHER NEGOTIATIONS (Direct with Pubs)                           │
│     └─ Agency negotiates PG deals with streaming publishers             │
│                                                                          │
│  3. DEAL ID COLLECTION (Email)                                          │
│     └─ Publishers email: Deal ID, SSP name, CPM, impressions           │
│                                                                          │
│  4. YAHOO DSP SETUP (Where Newton Helps!)                               │
│     └─ Register deals, create campaign/lines, assign targeting          │
│                                                                          │
│  5. INNOVID CREATIVE TAGGING                                            │
│     └─ Innovid generates VAST tags, assigned to placements             │
│                                                                          │
│  6. ACTIVATION                                                          │
│     └─ Campaign goes live                                               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Newton's Role

Newton automates **Step 4** - the tedious process of registering deals and configuring Yahoo DSP. Instead of manual data entry, you:
1. Tell Newton the deal details from your email
2. Newton registers deals and creates the campaign structure
3. Provide Innovid tag URLs
4. Newton assigns creatives and activates

---

## 📋 Demo Script

### Prerequisites

Connect Newton to your Yahoo DSP sales agent with proper authentication.

---

### Scene 1: Provide Prisma Context

**You Say:**
> "I have a Honda CR-V CTV campaign for Q1 2026. Budget is $2M. Here's our Prisma plan:
> - Disney (Disney+, Hulu, ESPN+) - 5M impressions - $150K
> - Paramount (Paramount+, Pluto) - 4M impressions - $100K
> - Tubi - 8M impressions - $80K
> - WBD (Max, Discovery+) - 4M impressions - $95K
> - Fox Sports - 3M impressions - $75K
> - Roku - 6M impressions - $120K
> - VEVO - 5M impressions - $60K
> - Vizio - 4M impressions - $45K
> - Samsung TV Plus - 3M impressions - $40K
> - LG Channels - 2M impressions - $35K
> 
> Campaign runs January 1 through March 31, 2026."

**Expected Newton Response:**
Newton should acknowledge the campaign plan and ask for the publisher deal IDs.

---

### Scene 2: Register First Deal (Creates Campaign)

**You Say:**
> "Disney sent us their deal: Deal ID DIS-PG-2026-HONDA, on FreeWheel. 5 million impressions at $30 CPM."

**Expected Newton Action:**
Newton calls `registerDeal`:
```json
{
  "deal_id": "DIS-PG-2026-HONDA",
  "publisher": "Disney",
  "impressions": 5000000,
  "cpm_rate": 30.00,
  "ssp": "FreeWheel",
  "campaign_name": "Honda CR-V CTV Q1 2026"
}
```

**Expected Response:**
Newton confirms:
- ✅ Deal registered
- ✅ Campaign "Honda CR-V CTV Q1 2026" created automatically
- ✅ Line item created for Disney

---

### Scene 3: Register Additional Deals

**You Say:**
> "Great! Here are the rest:
> - Paramount: PARA-PG-2026-HONDA on Magnite, 4M imps, $26.50 CPM
> - Tubi: TUBI-PG-2026-HONDA on Magnite, 8M imps, $10 CPM
> - WBD: WBD-PG-2026-HONDA on FreeWheel, 4M imps, $24 CPM
> - Fox Sports: FOX-PG-2026-HONDA on FreeWheel, 3M imps, $25 CPM
> - Roku: ROKU-PG-2026-HONDA on Magnite, 6M imps, $20 CPM
> - VEVO: VEVO-PG-2026-HONDA on SpotX, 5M imps, $12 CPM
> - Vizio: VIZIO-PG-2026-HONDA on PubMatic, 4M imps, $11 CPM
> - Samsung: SAMSUNG-PG-2026-HONDA on PubMatic, 3M imps, $13 CPM
> - LG: LG-PG-2026-HONDA on PubMatic, 2M imps, $17 CPM"

**Expected Newton Action:**
Newton calls `registerDeal` for each publisher, adding them to the existing campaign.

**Expected Response:**
Newton confirms all 10 deals registered:
- Campaign now has 10 deals
- Total budget: ~$800K (deal value based on imps × CPM)
- 10 line items created

---

### Scene 4: Review Campaign Structure

**You Say:**
> "Can you show me the campaign structure?"

**Expected Newton Action:**
Newton should describe the campaign:
- Campaign: Honda CR-V CTV Q1 2026
- Total deals: 10
- Total budget: $XXX
- Lines by publisher with budgets

---

### Scene 5: Register Innovid Creatives

**You Say:**
> "Our Innovid tags are ready:
> - 30s spot: https://search.spotxchange.com/vast/2.0/honda_crv_30s_2026
> - 15s spot: https://search.spotxchange.com/vast/2.0/honda_crv_15s_2026
> 
> Assign both to all lines."

**Expected Newton Action:**
Newton calls `registerInnovidTag` twice:
```json
{
  "tag_url": "https://search.spotxchange.com/vast/2.0/honda_crv_30s_2026",
  "name": "Honda CR-V 30s CTV 2026",
  "duration": 30,
  "line_ids": [all line IDs]
}
```

**Expected Response:**
Newton confirms:
- ✅ 30s creative registered and assigned to 10 lines
- ✅ 15s creative registered and assigned to 10 lines

---

### Scene 6: Activate Campaign

**You Say:**
> "Everything looks good. Let's activate the campaign."

**Expected Newton Action:**
Newton calls `activateCampaign` with the campaign ID.

**Expected Response:**
Newton confirms:
- ✅ Campaign activated
- ✅ Expected start: January 1, 2026
- ✅ All 10 lines active
- ✅ Budget pacing will begin at flight start

---

### Scene 7: Check Delivery (Post-Launch)

**You Say:**
> "How's the campaign pacing?"

**Expected Newton Action:**
Newton calls `getCampaignDelivery`.

**Expected Response:**
Newton provides delivery report:
- Total impressions delivered
- Spend by publisher
- VCR (video completion rate)
- Pacing status (ahead/behind/on-track)

---

## 🛠️ Available Tools

### Core Tools

| Tool | Purpose |
|------|---------|
| `registerDeal` | Register a PG deal from publisher email |
| `registerInnovidTag` | Register Innovid VAST tag as creative |
| `activateCampaign` | Activate campaign for delivery |
| `getCampaignDelivery` | Get delivery/pacing report |

### Discovery Tools (Reference Only)

| Tool | Purpose |
|------|---------|
| `listDeals` | List pre-existing deals (not used in agency workflow) |
| `getDealDetails` | Get deal info (not used in agency workflow) |

### Campaign Tools (Used Internally)

| Tool | Purpose |
|------|---------|
| `createCampaign` | Created automatically by first `registerDeal` |
| `createLine` | Created automatically by each `registerDeal` |
| `createAd` | Created automatically by `registerInnovidTag` |

---

## 📝 Key Differences from Previous Demo

| Previous Demo | New Agency Workflow |
|--------------|---------------------|
| Newton discovers pre-existing deals | User provides deal IDs from email |
| Newton creates campaign explicitly | First deal auto-creates campaign |
| Generic creative sync | Innovid VAST tag registration |
| Budget allocation decisions | Budget follows Prisma plan |
| Complex targeting setup | Targeting from Prisma/deal terms |

---

## 💡 Tips

1. **Prisma First**: Always start by sharing your Prisma plan with Newton
2. **Deal by Deal**: You can register deals one at a time or in batches
3. **Same Campaign**: All deals for one advertiser go to the same campaign
4. **Innovid Tags**: Get these from your creative team/Innovid portal
5. **Activation Last**: Only activate when all deals and creatives are ready

---

## 🚨 Troubleshooting

### "No tenant context"
- Ensure Newton is connected with proper authentication headers

### "Yahoo DSP only"
- These tools only work with Yahoo DSP adapter, not GAM/Mock

### Deal not found
- `registerDeal` creates new deals, it doesn't look up existing ones
- Use `listDeals` if you need to see what's already in the system
