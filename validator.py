import re

class ICE_Validator:
    def __init__(self, raw_content, filename):
        self.raw_content = raw_content
        self.filename = filename
        self.lines = raw_content.splitlines()
        self.errors = []
        self.warnings = []

    def run(self):
        if not self.lines:
            self.errors.append("File is empty.")
            return False

        self._check_filename()
        self._check_file_format()
        self._check_hdr()
        self._check_record_integrity()
        
        return len(self.errors) == 0

    def _check_filename(self):
        # Rule: CW[YY][nnnn]LUM_319.V22
        pattern = r"^CW\d{2}\d{4}LUM_319\.V22$"
        if not re.match(pattern, self.filename.strip(), flags=re.IGNORECASE):
            self.errors.append(f"Filename Error: '{self.filename}' does not match pattern CW[YY][nnnn]LUM_319.V22")

    def _check_file_format(self):
        # Rule: Windows CRLF (\r\n) per ICE standard
        if "\r\n" not in self.raw_content and "\n" in self.raw_content:
            self.errors.append("Format Error: Invalid line endings. ICE requires CRLF (\\r\\n).")

    def _check_hdr(self):
        if not self.lines[0].startswith("HDR"):
            self.errors.append("Critical: HDR record missing at Line 1.")
            return
        hdr = self.lines[0]
        # Offset 4-5: Sender Type '01'
        if hdr[3:5] != "01":
            self.errors.append(f"HDR Error: Sender Type at index 4 must be '01'. Found '{hdr[3:5]}'.")
        # Offset 60-64: EDI Version '01.10'
        if hdr[59:64] != "01.10":
            self.errors.append(f"HDR Alignment Error: '01.10' not found at index 60. Current value: '{hdr[59:64]}'.")

    def _check_record_integrity(self):
        """Strict coordinate validation based on Manual v2.2 and Approved Sample"""
        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            if not line.strip(): continue
            rectype = line[0:3]

            # 1. SPU Record (Strict 182 chars / Society Agreement Number check)
            if rectype == "SPU":
                if len(line) != 182:
                    self.errors.append(f"Line {line_num} (SPU): Invalid record length ({len(line)}). Must be 182.")
                
                agreement_no = line[166:180].strip()
                if agreement_no == "4316161":
                    self.warnings.append(f"Line {line_num} (SPU): Agreement '4316161' flagged as invalid in recent ACK.")

            # 2. REC Record (ISRC length and Validity Flag)
            if rectype == "REC":
                isrc = line[249:261].strip()
                if isrc:
                    if len(isrc) != 12:
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' is {len(isrc)} chars. Must be 12.")
                    if not isrc.startswith("USSHD"):
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' does not match Registrant Code 'USSHD'.")
                
                validity_flag = line[506:507]
                if validity_flag != 'Y':
                    self.errors.append(f"Line {line_num} (REC): ISRC Validity flag at index 507 must be 'Y'. Found '{validity_flag}'.")

            # 3. ORN Record (Numeric-only Cut Number)
            if rectype == "ORN":
                cut_number = line[97:101].strip()
                if cut_number and not cut_number.isdigit():
                    self.errors.append(f"Line {line_num} (ORN): Cut Number must be numeric. Found '{cut_number}'.")

            # 4. IPI Validation (SPU Index 88-98 / SWR Index 116-126)
            if rectype in ["SPU", "SWR"]:
                start = 87 if rectype == "SPU" else 115
                ipi = line[start:start+11].strip()
                if ipi and (not ipi.isdigit() or len(ipi) != 11):
                    self.errors.append(f"Line {line_num} ({rectype}): IPI '{ipi}' must be 11 numeric digits.")
