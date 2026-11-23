import re
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH

DOC_PATH = r"C:\Users\deep1\Downloads\thesis_draft_tobehuman_humanized.docx"

ALL_REFERENCES = [
    "[1] OECD, 'Education Policy Outlook 2025.' Available: https://www.oecd.org/en/publications/education-policy-outlook-2025_c3f402ba-en.html",
    "[2] Digital India Programme, Government of India. Available: https://www.digitalindia.gov.in",
    "[3] Press Information Bureau (PIB), Government of India, 'Digital India Statistics and Broadband Growth.' Available: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2241781",
    "[4] OECD, 'Digital Skills for Seniors,' 2025. Available: https://www.oecd.org/en/publications/digital-skills-for-seniors_9edfa7ef-en.html",
    "[5] UNFPA, 'India Ageing Report 2023: Caring for Our Elders - Institutional Responses,' United Nations Population Fund (UNFPA), New Delhi, India, 2023. Available: https://india.unfpa.org/en/publications/india-ageing-report-2023",
    "[6] K. M. Chacko et al., 'Digital Health and Literacy Intervention for Older Adults in Rural India (DAHLIA Study),' Geriatrics, vol. 7, no. 2, p. 32, 2022. Available: https://doi.org/10.3390/geriatrics7020032",
    "[7] J. A. G. van Dijk, 'Digital Divide Research: Achievements and Shortcomings,' Poetics, vol. 34, no. 4-5, pp. 221-235, 2006. Available: https://doi.org/10.1016/j.poetic.2006.05.004",
    "[8] Y. Tian and X. Mi, 'A Study of the Deconstruction and Construction of Self-Efficacy in Internet Use Among Older People,' BMC Geriatrics, vol. 25, no. 1, p. 120, 2025. Available: https://doi.org/10.1186/s12877-025-05703-9",
    "[9] C. Lee and J. F. Coughlin, 'Older Adults' Adoption of Technology: An Integrated Approach to Identifying Determinants and Barriers to Technology Use,' Journal of Product Innovation Management, vol. 32, no. 5, pp. 747-759, 2015. Available: https://doi.org/10.1111/jpim.12176",
    "[10] F. Ezeudoka and W. Fan, 'Exploring the Impact of Digital Distrust on User Resistance to E-Health Services Among Older Adults,' Humanities and Social Sciences Communications, vol. 11, no. 1, p. 450, 2024. Available: https://doi.org/10.1057/s41599-024-03248-w",
    "[11] H. Kim, 'Impact of Cybersecurity Self-Efficacy on Digital Economic Behaviors Among Older Adults,' SAGE Open, vol. 15, no. 1, pp. 1-14, 2025. Available: https://doi.org/10.1177/21582440251314660",
    "[12] J. W. Creswell, M. D. Fetters, and N. V. Ivankova, 'Designing a mixed methods study in primary care,' Annals of Family Medicine, vol. 2, no. 1, pp. 7-12, 2004. Available: https://doi.org/10.1370/afm.104",
    "[13] M. D. Fetters, L. A. Curry, and J. W. Creswell, 'Achieving integration in mixed methods designs - principles and practices,' Health Services Research, vol. 48, no. 6, pp. 2134-2156, 2013. Available: https://doi.org/10.1111/1475-6773.12114",
    "[14] British Design Council, 'The Design Process: What is the Double Diamond?,' Design Council UK, 2019. Available: https://www.designcouncil.org.uk/our-resources/the-double-diamond/",
    "[15] J. Zimmerman, J. Forlizzi, and S. Evenson, 'Research through design as a method for interaction design research in HCI,' in Proc. SIGCHI Conf. Hum. Factors Comput. Syst. (CHI '07), San Jose, CA, 2007, pp. 493-502. Available: https://doi.org/10.1145/1240624.1240704",
    "[16] V. Braun and V. Clarke, 'Using thematic analysis in psychology,' Qual. Res. Psychol., vol. 3, no. 2, pp. 77-101, 2006. Available: https://doi.org/10.1191/1478088706qp063oa",
    "[17] National Payments Corporation of India (NPCI), 'UPI Product Statistics and Monthly Metrics,' NPCI Official Portal, 2024. Available: https://www.npci.org.in/what-we-do/upi/product-statistics",
    "[18] A. Bandura, Self-Efficacy: The Exercise of Control. New York, NY: W. H. Freeman and Company, 1997. Available: https://psycnet.apa.org/record/1997-08589-000",
    "[19] F. D. Davis, 'Perceived usefulness, perceived ease of use, and user acceptance of information technology,' MIS Quarterly, vol. 13, no. 3, pp. 319-340, 1989. Available: https://doi.org/10.2307/249008",
    "[20] R. A. Bauer, 'Consumer behavior as risk taking,' in Dynamic Marketing for a Changing World, R. S. Hancock, Ed. Chicago, IL: American Marketing Association, 1960, pp. 389-398. Available: https://www.jstor.org/stable/j.ctt1g69x44",
    "[21] M. J. Kim et al., 'Technophobia in Digital Health Contexts Among Older Adults: Systematic Review and Meta-Analysis,' Journal of Medical Internet Research, vol. 25, e41250, 2023. Available: https://doi.org/10.2196/41250",
    "[22] D. A. Norman, The Design of Everyday Things: Revised and Expanded Edition. New York, NY: Basic Books, 2013. Available: https://jnd.org/the-design-of-everyday-things-revised-and-expanded-edition/",
    "[23] T. A. Salthouse, 'The processing-speed theory of adult age differences in cognition,' Psychol. Rev., vol. 103, no. 3, pp. 403-428, 1996. Available: https://doi.org/10.1037/0033-295X.103.3.403",
    "[24] S. J. Czaja et al., 'Touchscreen Manipulation and Performance Across Age Cohorts in Community-Dwelling Adults,' Human Factors, vol. 63, no. 4, pp. 612-628, 2021. Available: https://doi.org/10.1177/0018720819896778",
    "[25] P. M. Fitts, 'The information capacity of the human motor system in controlling the amplitude of movement,' J. Exp. Psychol., vol. 47, no. 6, pp. 381-391, 1954. Available: https://doi.org/10.1037/h0055392",
    "[26] C. Gomez-Hernandez et al., 'Design Guidelines of Mobile Apps for Older Adults: Systematic Review and Thematic Analysis,' International Journal of Human-Computer Interaction, vol. 39, no. 8, pp. 1-19, 2023. Available: https://doi.org/10.1080/10447318.2022.2078426",
    "[27] World Wide Web Consortium (W3C), 'Web Content Accessibility Guidelines (WCAG) 2.2,' W3C Recommendation, Oct. 2023. Available: https://www.w3.org/TR/WCAG22/",
    "[28] World Wide Web Consortium (W3C), 'Making Content Usable for People with Cognitive and Learning Disabilities,' W3C Working Group Note, Apr. 2021. Available: https://www.w3.org/TR/coga-usable/",
    "[29] L. Nurgalieva et al., 'Touchscreen Design Guidelines for Older Adults: A Systematic Literature Review,' ACM Computing Surveys, vol. 52, no. 3, pp. 1-36, 2019. Available: https://doi.org/10.1145/3318116",
    "[30] J. Bailey et al., 'Mobile Interface Design for Older Adults: A Communication Process Perspective,' Interacting with Computers, vol. 31, no. 5, pp. 450-467, 2019. Available: https://doi.org/10.1093/iwc/iwz031",
    "[31] Apple Inc., 'Human Interface Guidelines: Designing for Accessibility,' Apple Developer Documentation, 2024. Available: https://developer.apple.com/design/human-interface-guidelines/accessibility",
    "[32] Google LLC, 'Material Design 3: Accessibility & Inclusive Design,' Material Design Guidelines, 2024. Available: https://m3.material.io/foundations/accessible-design/overview",
    "[33] A. Paivio, Mental Representations: A Dual Coding Approach. Oxford, U.K.: Oxford University Press, 1986. Available: https://doi.org/10.1093/acprof:oso/9780195066661.001.0001",
    "[34] M. W. Someren, Y. F. Barnard, and J. A. C. Sandberg, The Think Aloud Method: A Practical Guide to Modelling Cognitive Processes. London, U.K.: Academic Press, 1994. Available: https://pure.uva.nl/ws/files/1660161/14878_someren.pdf",
    "[35] J. Brooke, 'SUS: A quick and dirty usability scale,' in Usability Evaluation in Industry, P. W. Jordan, B. Thomas, I. L. McClelland, and B. Weerdmeester, Eds. London, U.K.: Taylor & Francis, 1996, pp. 189-194. Available: https://www.usability.gov/how-to-and-tools/methods/system-usability-scale.html",
    "[36] Reserve Bank of India (RBI), 'Master Direction - Digital Payment Security Controls,' RBI Notifications, 2021. Available: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12032"
]

def set_para_text(p, text):
    if not p.runs:
        p.text = text
        return
    first = p.runs[0]
    first.text = text
    for r in p.runs[1:]:
        r.text = ""

def fix_document():
    doc = docx.Document(DOC_PATH)
    paras = doc.paragraphs

    # 1. Fix in-text citations in Chapter 1.1 (P11 & P12)
    # P11: Add [1] and [2] to restore sequential IEEE order
    p11_text = paras[11].text
    if "[1]" not in p11_text and "[3]" in p11_text:
        p11_text = p11_text.replace("participate in digital services.", "participate in digital services [1].")
        p11_text = p11_text.replace("DigiLocker and e-governance.", "DigiLocker and e-governance [2].")
        set_para_text(paras[11], p11_text)
        print("Fixed P11 citations: added [1] and [2]")

    # P12: Clean orphan text " Benefits" at end if present
    p12_text = paras[12].text
    if p12_text.endswith(" Benefits"):
        p12_text = p12_text[:-len(" Benefits")].strip()
        set_para_text(paras[12], p12_text)
        print("Cleaned orphan ' Benefits' from P12")

    # 2. Fix P53 leading bullet char in normal style
    p53_text = paras[53].text
    if p53_text.startswith("• "):
        set_para_text(paras[53], p53_text[2:].strip())
        print("Stripped leading bullet glyph from P53")

    # 3. Fix 1.7 Scope of the Dissertation (P62 to P67)
    # Ensure numbered points 1 to 6 without bullet style
    scope_texts = [
        "1. Geographical Scope: The study is situated in India and focuses on the experiences of senior citizens using digital services within the Indian social, cultural, and technological context.",
        "2. Target Audience: The study focuses on senior citizens in India who have some experience with smartphones and internet-based services but remain hesitant or dependent during transactional tasks.",
        "3. Digital Service Contexts: Six everyday digital service areas in India were examined: UPI payments, digital banking, healthcare booking, ride-hailing, e-commerce, and government forms.",
        "4. Research Focus: The study investigates the Digital Confidence Gap and factors that influence confidence, including fear of mistakes, perceived risk, reassurance, and process clarity.",
        "5. Interaction Design Focus: The study explores design approaches such as step-by-step guidance, consequence transparency, reassurance prompts, and reversible error recovery.",
        "6. Research and Design Outcome: Surveys, interviews, and secondary research informed user requirements and the design of an interactive prototype for senior citizens."
    ]
    for idx, stxt in enumerate(scope_texts):
        p_target = paras[62 + idx]
        set_para_text(p_target, stxt)
        p_target.style = doc.styles["Normal"]
        p_target.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    print("Fixed 1.7 Scope items 1-6 formatting and styles")

    # 4. Fix 1.8 Limitations of the Dissertation (P68 is heading, P69-P73 are items)
    limitations_texts = [
        "1. Geographical Limitation: The study focuses on India; therefore, its findings may not apply directly to other countries, given differences in digital infrastructure, service design, regulatory environments, and cultural contexts.",
        "2. Limited Sample Representation: The research sample may not represent the diversity of senior citizens across India, particularly differences in age, education, income, language, location, and digital experience.",
        "3. Variation Across Digital Services: Different digital services have different interfaces, risk profiles, and cognitive demands; findings from the six focal areas may not generalize to all digital platforms.",
        "4. Prototype Evaluation Constraints: Evaluation using a limited prototype and selected tasks may not fully reflect real-world conditions or establish long-term improvements in digital confidence and independence.",
        "5. External Factors: Device access, internet connectivity, digital literacy, accessibility needs, language differences, and social support can influence digital inclusion but are not the primary focus of this dissertation."
    ]
    for idx, ltxt in enumerate(limitations_texts):
        p_target = paras[69 + idx]
        set_para_text(p_target, ltxt)
        p_target.style = doc.styles["Normal"]
        p_target.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    print("Fixed 1.8 Limitations items 1-5 formatting and styles")

    # 5. Fix 1.9 Significance of the Study (P74 is heading, P75-P78 are items)
    significance_texts = [
        "For society, this research is relevant to supporting senior citizens amid an ageing population. With over 20% of India's population projected to be aged 60+ by 2050 [5], identifying design factors that foster confidence and independent engagement is essential for sustainable digital public services.",
        "For designers and developers, this study provides insights into how interaction design affects confidence in older adults, offering actionable design heuristics, interaction patterns, and an open-source reference prototype to guide age-inclusive product development.",
        "For policy and organisations, findings can help inform digital inclusion strategies. While many current efforts focus on digital skills and infrastructure, this research shows that confidence and independence are also important to consider. Recognising this can help create more effective digital inclusion programs.",
        "Overall, this research helps understand how interaction design can support older adults in being confident and independent when using digital services. By addressing the Digital Confidence Gap, this study supports efforts towards digital equity and inclusion."
    ]
    for idx, sigtxt in enumerate(significance_texts):
        p_target = paras[75 + idx]
        set_para_text(p_target, sigtxt)
        p_target.style = doc.styles["Normal"]
        p_target.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # Blank out redundant P79 if it duplicates P76/P78
    if paras[79].text.strip().startswith("Overall, this research helps understand"):
        # Make P79 empty and let Chapter Summary follow cleanly
        set_para_text(paras[79], "")
    print("Fixed 1.9 Significance items and removed duplicate paragraph")

    # 6. Global scan for duplicate bullets, literal bullets in list styles, and justified headings
    bullet_re = re.compile(r"^[\s\u2022\u25cf\u25cb\u25aa\u25ab\u2023\u2043\*\-\–\—\•]+\s*")
    for i, p in enumerate(paras):
        s_name = p.style.name.lower() if p.style else ""
        txt = p.text.strip()
        if not txt:
            continue
        
        # Strip literal bullet if style is already a list/bullet style
        if any(k in s_name for k in ["bullet", "list"]):
            if bullet_re.match(txt):
                cleaned = bullet_re.sub("", txt).strip()
                set_para_text(p, cleaned)
            # If paragraph in bullet style starts with a number like "1. ", convert style to Normal
            if re.match(r"^\d+[\.\)]\s+", p.text.strip()):
                p.style = doc.styles["Normal"]
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # Check justified short headings (< 15 words) that shouldn't be stretched across page
        words = len(txt.split())
        if words <= 14 and p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
            if not txt.endswith((".", "!", "?")) or txt.endswith(":"):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    print("Global cleanup of duplicate bullets and justified headings completed")

    # 7. Fix REFERENCES Section (P683 to P719)
    # P683 is heading 'REFERENCES'
    ref_start = None
    for i, p in enumerate(paras):
        if p.text.strip().upper() == "REFERENCES":
            ref_start = i
            break
    
    if ref_start is not None:
        print(f"Rebuilding REFERENCES section starting at P{ref_start + 1}")
        for k in range(len(ALL_REFERENCES)):
            target_p = paras[ref_start + 1 + k]
            set_para_text(target_p, ALL_REFERENCES[k])
            target_p.style = doc.styles["Normal"]
            target_p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # 8. Fix Appendices A and B (Restore original text where citations leaked)
    p725 = paras[725]
    set_para_text(p725, "Purpose of Study: You are invited to participate in a research study investigating the Digital Confidence Gap among senior citizens in India. The purpose is to understand barriers to independent digital service usage and evaluate inclusive interaction design interventions.")
    p725.style = doc.styles["Normal"]
    p725.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    p726 = paras[726]
    set_para_text(p726, "Ethical Safeguards & Data Privacy: 1) All tasks in this study involving payments or sensitive credentials utilize a secure, sandboxed simulation environment; no real money or confidential credentials are ever accessed or stored. 2) All qualitative responses and survey telemetry are fully anonymized. 3) Participation is voluntary, and you may withdraw at any time without penalty.")
    p726.style = doc.styles["Normal"]
    p726.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    p732 = paras[732]
    set_para_text(p732, "Primary Reasons for Seeking Help: Fear of mistakes (62.3%), Fear of scams (49.2%), Lack of confidence (48.5%), Confusing interfaces (47.7%), Difficulty understanding instructions (47.7%), Forgetting steps (46.9%), Difficulty reading text (20.8%).")
    p732.style = doc.styles["List Bullet"]
    p732.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    print("Restored original text in Appendices A and B (P725, P726, P732)")

    # Save fixed document
    doc.save(DOC_PATH)
    print(f"Successfully saved fixed document to {DOC_PATH}")

if __name__ == "__main__":
    fix_document()
