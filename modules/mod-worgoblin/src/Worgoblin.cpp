#include "Player.h"
#include "ScriptMgr.h"
#include "SpellScript.h"

enum Spells
{
    BEST_DEALS_ANYWHERE   = 69044,
    TWO_FORMS_MALE        = 68995, // transforms to CreatureDisplayInfo 20707 (Human male)
    TWO_FORMS_FEMALE      = 68996, // transforms to CreatureDisplayInfo 20708 (Human female)
};

namespace
{
    constexpr uint8 WORGEN_RACE_ID         = 12;
    constexpr uint8 TWO_FORMS_ACTION_SLOT  = 11;
}

class worgoblin : public PlayerScript {

public:
    worgoblin() : PlayerScript("worgoblin") { }

    void OnPlayerLogin(Player* player) override
    {
        // Two Forms (68995/68996) ships as a pair of gender-specific
        // transform spells, each hard-coded to a single Human
        // CreatureDisplayInfo (20707 male / 20708 female). Their
        // SkillLineAbility rows both carry AcquireMethod=2 with
        // RaceMask=2048, so Player::learnSkillRewardedSpells auto-grants
        // BOTH variants as PLAYERSPELL_TEMPORARY to every Worgen at login.
        // The auto-grant runs from _LoadSkills which is called before this
        // hook, so by the time we get here m_spells already has both copies
        // (and SMSG_INITIAL_SPELLS would send both, showing two "Two Forms"
        // entries in the spellbook). Drop the gender-wrong variant -- only
        // the temporary copy, never anything actually persisted.
        if (player->getRace() == WORGEN_RACE_ID)
        {
            uint32 const wrongVariant = (player->getGender() == GENDER_FEMALE)
                                        ? TWO_FORMS_MALE
                                        : TWO_FORMS_FEMALE;
            player->removeSpell(wrongVariant, SPEC_MASK_ALL, /*onlyTemporary*/ true);
        }
    }

    // Slot the gender-correct Two Forms on the action bar at first login.
    // The spell itself is auto-granted via learnSkillRewardedSpells (see
    // OnPlayerLogin); this hook just makes the default action-bar button
    // point at the right variant so new chars don't have to drag it.
    void OnPlayerFirstLogin(Player* player) override
    {
        if (player->getRace() != WORGEN_RACE_ID)
            return;

        uint32 const twoForms = (player->getGender() == GENDER_FEMALE)
                                ? TWO_FORMS_FEMALE
                                : TWO_FORMS_MALE;

        player->addActionButton(TWO_FORMS_ACTION_SLOT, twoForms, ACTION_BUTTON_SPELL);
    }

    void OnPlayerGetReputationPriceDiscount(Player const* player, FactionTemplateEntry const* factionTemplate, float& discount) override
    {
        if (!factionTemplate || !factionTemplate->faction)
            return;

        if (player->HasSpell(BEST_DEALS_ANYWHERE))
            discount *= 0.8;
    }
};

class spell_rocket_barrage : public SpellScript
{
    PrepareSpellScript(spell_rocket_barrage);

    void HandleDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        int32 basePoints = 0 + caster->GetLevel() * 2;
        basePoints += caster->SpellBaseDamageBonusDone(GetSpellInfo()->GetSchoolMask()) * 0.429; //BM=0.429 here, don't ask me how.
        basePoints += caster->GetTotalAttackPowerValue(caster->getClass() != CLASS_HUNTER ? BASE_ATTACK : RANGED_ATTACK) * 0.25; // 0.25=BonusCoefficient, hardcoding it here
        SetEffectValue(basePoints);
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_rocket_barrage::HandleDamage, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

void Add_Worgoblin()
{
    new worgoblin();
    RegisterSpellScript(spell_rocket_barrage);
}
