import re

class ICE_Validator:
    def __init__(self, raw_content, filename):
        self.raw_content = raw_content
        self.filename = filename
        self.lines = raw_content.splitlines()
        self.errors = []

    def run(self):
        self._check_records_and_math()
        return len(self.errors) == 0

    def _check_records_and_math(self):
        current_work = None
        pr_total = mr_total = sr_total = 0

        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            if not line.strip(): continue
            rectype = line[0:3]

            # Reset math on new work
            if rectype in ["NWR", "REV"]:
                if current_work: self._validate_share_totals(current_work, pr_total, mr_total, sr_total)
                current_work = f"Line {line_num}"; pr_total = mr_total = sr_total = 0

            elif rectype == "SPU":
                # ABSOLUTE POSITIONS: PR(116-120), MR(124-128), SR(132-136)
                pr, mr, sr = self._extract_shares(line, 115, 123, 131)
                pr_total += pr; mr_total += mr; sr_total += sr

            elif rectype == "SWR":
                # ABSOLUTE POSITIONS: PR(130-134), MR(138-142), SR(146-150)
                pr, mr, sr = self._extract_shares(line, 129, 137, 145)
                pr_total += pr; mr_total += mr; sr_total += sr

        if current_work: self._validate_share_totals(current_work, pr_total, mr_total, sr_total)

    def _extract_shares(self, line, pr_start, mr_start, sr_start):
        # Extract exactly 5 digits for each share
        pr = int(line[pr_start:pr_start+5].strip() or 0)
        mr = int(line[mr_start:mr_start+5].strip() or 0)
        sr = int(line[sr_start:sr_start+5].strip() or 0)
        return pr, mr, sr

    def _validate_share_totals(self, work_id, pr, mr, sr):
        if pr != 10000: self.errors.append(f"{work_id}: PR total {pr} != 10000")
        if mr != 10000: self.errors.append(f"{work_id}: MR total {mr} != 10000")
        if sr != 10000: self.errors.append(f"{work_id}: SR total {sr} != 10000")
