import type { PriorAuthRequest } from "./types";

export const SAMPLE_REQUEST: PriorAuthRequest = {
  patient_name: "John Smith",
  patient_dob: "1958-03-15",
  provider_npi: "1902809042",
  diagnosis_codes: ["R91.1", "J18.9", "R05.9"],
  procedure_codes: ["31628"],
  clinical_notes:
    "68-year-old male with persistent right lower lobe pulmonary nodule " +
    "identified on CT chest (1.8 cm, spiculated margins). History of 40 " +
    "pack-year smoking, quit 5 years ago. PET scan shows SUV of 4.2. " +
    "Patient completed course of antibiotics with no resolution. Prior " +
    "CT 3 months ago showed interval growth from 1.2 cm. Pulmonary " +
    "function tests: FEV1 78% predicted. No prior history of malignancy. " +
    "Recommend CT-guided transbronchial lung biopsy for tissue diagnosis " +
    "given high suspicion for malignancy per Fleischner Society guidelines.",
  insurance_id: "MCR-123456789A",
};
