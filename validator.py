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
        self._check_transactions()
        
        return len(self.errors) == 0

    def _check_filename(self):
        # Strict ICE Filename Format: CW[YY][nnnn]LUM_319.V22
        # ^ ensures it starts exactly with CW, $ ensures it ends exactly with .V22
        pattern = r"^CW\d{2}\d{4}LUM_319\.V22$"
        
        clean_name = self.filename.strip()
        
        if not re.match(pattern, clean_name, flags=re.IGNORECASE):
            self.errors.append(
                f"Filename Error: '{clean_name}' violates strict naming convention. "
                f"Must be exactly 'CW[YY][nnnn]LUM_319.V22' (e.g., CW260003LUM_319.V22). "
                f"Remove any album codes or '.txt' extensions."
            )

    def _check_file_format(self):
        # Chris's file uses strict Windows CRLF
        if "\r\n" not in self.raw_content and "\n" in self.raw_content:
            self.errors.append("Format Error: File uses UNIX (\\n) line endings. ICE requires CRLF (\\r\\n).")

    def _check_hdr(self):
        hdr = self.lines[0]
        if not hdr.startswith("HDR"):
            self.errors.append("Critical: File must start with HDR.")
            return

        # ICE Manual: Sender Type must be '01'
        if hdr[3:5] != "01":
            self.errors.append(f"HDR Error: Sender Type is '{hdr[3:5]}'. ICE strictly requires '01'.")

        # Alignment Check
        if len(hdr) >= 64:
            edi_version = hdr[59:64]
            if edi_version != "01.10":
                self.errors.append(f"HDR Alignment Error: Expected '01.10' at index 60. Found '{edi_version}'. Check Sender Name padding.")

    def _check_transactions(self):
        current_grh_type = None

        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            if not line.strip(): continue
            
            rectype = line[0:3]

            # 1. GRH / Transaction Matching
            if rectype == "GRH":
                current_grh_type = line[3:6].strip()
            
            if rectype in ["NWR", "REV"]:
                if current_grh_type and rectype != current_grh_type:
                    self.errors.append(f"Line {line_num} ({rectype}): Transaction type does not match GRH declaration '{current_grh_type}'.")

            # 2. SPU Blueprint (Based on Chris's Approved File)
            if rectype == "SPU":
                if len(line) != 182:
                    self.errors.append(f"Line {line_num} (SPU): Length is {len(line)}. ICE expects exactly 182 characters based on the approved blueprint.")

            # 3. SPT ICE Overrides
            if rectype == "SPT":
                if len(line) >= 50:
                    inclusion_ind = line[49:50]
                    if inclusion_ind not in ["I", "E"]:
                        self.errors.append(f"Line {line_num} (SPT): Inclusion/Exclusion indicator at index 50 must be 'I' or 'E'. Found '{inclusion_ind}'.")
