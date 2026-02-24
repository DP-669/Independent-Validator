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
        self._check_data_cleanliness()
        
        return len(self.errors) == 0

    def _check_filename(self):
        # Strict ICE Filename Format: CW[YY][nnnn]LUM_319.V22
        pattern = r"^CW\d{2}\d{4}LUM_319\.V22$"
        clean_name = self.filename.strip()
        if not re.match(pattern, clean_name, flags=re.IGNORECASE):
            self.errors.append(
                f"Filename Error: '{clean_name}' violates convention. "
                f"Must be exactly 'CW[YY][nnnn]LUM_319.V22' (e.g., CW260003LUM_319.V22)."
            )

    def _check_file_format(self):
        if "\r\n" not in self.raw_content and "\n" in self.raw_content:
            self.errors.append("Format Error: ICE requires Windows CRLF (\\r\\n).")

    def _check_hdr(self):
        if not self.lines[0].startswith("HDR"):
            self.errors.append("Critical: File must start with HDR.")
            return
        hdr = self.lines[0]
        if hdr[3:5] != "01":
            self.errors.append(f"HDR Error: Sender Type must be '01'.")
        if hdr[59:64] != "01.10":
            self.errors.append("HDR Alignment Error: '01.10' not found at index 60. Check padding.")

    def _check_data_cleanliness(self):
        """Business Logic Layer to catch Berlin 'Data Cleaning' rejections"""
        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            if not line.strip(): continue
            rectype = line[0:3]

            # 1. ISRC CLEANING (RECF010 / RECF018)
            if rectype == "REC":
                isrc = line[249:261].strip()
                if isrc:
                    # Length Check
                    if len(isrc) != 12:
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' is {len(isrc)} chars. Must be 12.")
                    
                    # Prefix Check (Lumina Specific)
                    if not isrc.startswith("USSHD"):
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' must start with 'USSHD' per RIAA assignment.")
                    
                    # Validity Flag (Index 507)
                    validity_flag = line[506:507]
                    if validity_flag != 'Y':
                        self.errors.append(f"Line {line_num} (REC): ISRC Validity must be 'Y'. Found '{validity_flag}'.")

            # 2. ORN CUT NUMBER CLEANING (ORNF005)
            if rectype == "ORN":
                cut_number = line[97:101].strip()
                if cut_number and not cut_number.isdigit():
                    self.errors.append(f"Line {line_num} (ORN): Cut Number '{cut_number}' must be numeric (found '{cut_number}').")

            # 3. IPI VALIDATION
            if rectype in ["SPU", "SWR"]:
                start = 87 if rectype == "SPU" else 115
                ipi = line[start:start+11].strip()
                if ipi:
                    if not ipi.isdigit() or len(ipi) != 11:
                        self.errors.append(f"Line {line_num} ({rectype}): IPI '{ipi}' must be exactly 11 numeric digits.")

            # 4. SPU RULES
            if rectype == "SPU":
                if len(line) != 182:
                    self.errors.append(f"Line {line_num} (SPU): Length is {len(line)}, must be 182.")
                
                # Warning for the flagged Agreement ID
                agreement_no = line[166:180].strip()
                if agreement_no == "4316161":
                    self.warnings.append(f"Line {line_num} (SPU): Agreement '4316161' is still active but was flagged by Berlin.")
