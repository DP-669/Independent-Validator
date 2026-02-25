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
            self.errors.append("Critical: File is empty.")
            return False

        self._check_filename()
        self._check_file_format()
        self._check_hdr()
        self._check_records_and_math()
        
        return len(self.errors) == 0

    def _check_filename(self):
        pattern = r"^CW\d{2}\d{4}LUM_319\.V22$"
        if not re.match(pattern, self.filename.strip(), flags=re.IGNORECASE):
            self.errors.append(f"Filename Error: '{self.filename}' violates CW[YY][nnnn]LUM_319.V22 convention.")

    def _check_file_format(self):
        if "\r\n" not in self.raw_content and "\n" in self.raw_content:
            self.errors.append("Format Error: Invalid line endings. CWR v2.2 strictly requires CRLF (\\r\\n).")

    def _check_hdr(self):
        hdr = self.lines[0]
        if not hdr.startswith("HDR"):
            self.errors.append("Critical: File does not start with an HDR record.")
            return
        
        if hdr[3:5] != "01":
            self.errors.append(f"HDR Error: Sender Type (Pos 4-5) must be '01'. Found '{hdr[3:5]}'.")
            
        if hdr[59:64] != "01.10":
            self.errors.append(f"HDR Alignment Error: EDI Version '01.10' (Pos 60-64) missing. Found '{hdr[59:64]}'.")

    def _check_records_and_math(self):
        current_work = None
        pr_total = 0
        mr_total = 0
        sr_total = 0

        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            if not line.strip(): continue
            rectype = line[0:3]

            # TRANSACTION TRACKING (NWR/REV)
            if rectype in ["NWR", "REV"]:
                if current_work is not None:
                    self._validate_share_totals(current_work, pr_total, mr_total, sr_total)
                
                current_work = f"Line {line_num} ({rectype})"
                pr_total = mr_total = sr_total = 0

            # SPU: PUBLISHER RECORD
            elif rectype == "SPU":
                if len(line) != 182:
                    self.errors.append(f"Line {line_num} (SPU): Invalid record length ({len(line)}). Must be exactly 182 chars.")
                
                # IPI Validation
                ipi = line[87:98].strip()
                if ipi and (not ipi.isdigit() or len(ipi) != 11):
                    self.errors.append(f"Line {line_num} (SPU): IPI '{ipi}' at Pos 88-98 must be exactly 11 numeric digits.")

                # SPU Ownership Shares
                pr, mr, sr = self._extract_shares(line, 115, 123, 131, line_num, "SPU")
                pr_total += pr; mr_total += mr; sr_total += sr

            # SWR: WRITER RECORD
            elif rectype == "SWR":
                # IPI Validation
                ipi = line[115:126].strip()
                if ipi and (not ipi.isdigit() or len(ipi) != 11):
                    self.errors.append(f"Line {line_num} (SWR): IPI '{ipi}' at Pos 116-126 must be exactly 11 numeric digits.")

                # SWR Ownership Shares
                pr, mr, sr = self._extract_shares(line, 129, 137, 145, line_num, "SWR")
                pr_total += pr; mr_total += mr; sr_total += sr

            # SPT: PUBLISHER TERRITORY
            elif rectype == "SPT":
                inclusion = line[49:50]
                if inclusion not in ["I", "E"]:
                    self.errors.append(f"Line {line_num} (SPT): Inclusion/Exclusion (Pos 50) must be 'I' or 'E'. Found '{inclusion}'.")

            # REC: RECORDING DETAILS
            elif rectype == "REC":
                isrc = line[249:261].strip()
                if isrc:
                    if len(isrc) != 12:
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' at Pos 250-261 must be exactly 12 chars.")
                    if not isrc.startswith("USSHD"):
                        self.errors.append(f"Line {line_num} (REC): ISRC '{isrc}' must start with 'USSHD'.")
                
                validity = line[506:507]
                if validity != 'Y':
                    self.errors.append(f"Line {line_num} (REC): ISRC Validity (Pos 507) must be 'Y'. Found '{validity}'.")

            # ORN: WORK ORIGIN
            elif rectype == "ORN":
                cut_no = line[97:101].strip()
                if cut_no and not cut_no.isdigit():
                    self.errors.append(f"Line {line_num} (ORN): Cut Number (Pos 98-101) must be strictly numeric. Found '{cut_no}'.")

        # Validate final work's totals
        if current_work is not None:
            self._validate_share_totals(current_work, pr_total, mr_total, sr_total)

    def _extract_shares(self, line, pr_idx, mr_idx, sr_idx, line_num, rec_type):
        """Extracts 5-digit ownership shares securely using precise absolute indexing"""
        try:
            pr_str = line[pr_idx:pr_idx+5].strip()
            mr_str = line[mr_idx:mr_idx+5].strip()
            sr_str = line[sr_idx:sr_idx+5].strip()

            pr = int(pr_str) if pr_str else 0
            mr = int(mr_str) if mr_str else 0
            sr = int(sr_str) if sr_str else 0
            
            if pr > 10000 or mr > 10000 or sr > 10000:
                 self.errors.append(f"Line {line_num} ({rec_type}): Individual share exceeds 10000 (100%). PR:{pr}, MR:{mr}, SR:{sr}")
            return pr, mr, sr

        except ValueError:
            self.errors.append(f"Line {line_num} ({rec_type}): Non-numeric character found in share fields.")
            return 0, 0, 0

    def _validate_share_totals(self, work_id, pr_total, mr_total, sr_total):
        """Validates that total ownership equals exactly 100% (10000)"""
        if pr_total != 10000:
            self.errors.append(f"Work starting at {work_id}: Total Performance (PR) shares equal {pr_total}. Must be exactly 10000.")
        if mr_total != 10000:
            self.errors.append(f"Work starting at {work_id}: Total Mechanical (MR) shares equal {mr_total}. Must be exactly 10000.")
        if sr_total != 10000:
            self.errors.append(f"Work starting at {work_id}: Total Sync (SR) shares equal {sr_total}. Must be exactly 10000.")
