import os
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

# Configuration for your specific environment
NMAP_PATH = "/opt/homebrew/bin/nmap"
NUCLEI_PATH = "/opt/homebrew/bin/nuclei"

def run_command(command, description, use_sudo=False):
    if use_sudo:
        command = f"sudo {command}"
    
    print(f"[+] Running {description}...")
    try:
        # Using shell=True to handle sudo and pathing easily
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[-] Error during {description}: {e}")
        print(f"[-] Stderr: {e.stderr}")
        return ""

def analyze_with_ai(scan_data):
    if not scan_data.strip():
        return "No scan data captured to analyze."

    print("[+] Sending data to AI for vendor patch validation...")
    
    prompt = f"""
    Act as a Senior Network Security Engineer. Analyze the following scan data for Cisco devices:
    
    {scan_data}
    
    Tasks:
    1. Identify exact OS versions (IOS, IOS-XE, ASA, etc.) from the fingerprints.
    2. Cross-reference these versions against known Cisco Security Advisories (up to 2026) for NTP, SNMP, and SSH.
    3. Determine if the firmware level is 'confirmed vulnerable' or 'likely vulnerable' based on vendor patches.
    4. Provide a consolidated table of Host, Port, Service, and Vulnerability Status.
    5. Suggest specific remediation (e.g., 'no snmp-server', 'ntp access-group', or 'ip access-list' examples).
    """

    # OpenAI Logic
    if os.getenv("OPENAI_API_KEY"):
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    # Google Gemini Logic
    elif os.getenv("GOOGLE_API_KEY"):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    
    else:
        return "Error: No API credentials found in .env or Environment Variables."

def main():
    target_file = "targets.txt"
    if not os.path.exists(target_file):
        print(f"[-] Error: {target_file} not found. Please create it with one IP per line.")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Nmap Fingerprinting (Requires Root/Sudo)
    # -sV: Version detection, -O: OS detection
    nmap_cmd = f"{NMAP_PATH} -sV -O -p 22,123,161 --open -iL {target_file}"
    nmap_results = run_command(nmap_cmd, "Nmap (Root privileges required)", use_sudo=True)

    # 2. Nuclei Vulnerability Scan
    nuclei_cmd = f"{NUCLEI_PATH} -l {target_file} -tags ssh,snmp,ntp -severity critical,high,medium"
    nuclei_results = run_command(nuclei_cmd, "Nuclei Scanning")

    # 3. AI Analysis
    combined_data = f"--- NMAP RESULTS ---\n{nmap_results}\n\n--- NUCLEI RESULTS ---\n{nuclei_results}"
    
    final_report = analyze_with_ai(combined_data)
    
    # Save Final Consolidated Report
    report_filename = f"remediation_report_{timestamp}.md"
    with open(report_filename, "w") as f:
        f.write(f"# Revvity Security Validation Report\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write(final_report)

    print(f"\n[!] Success! Final remediation report saved to: {report_filename}")

if __name__ == "__main__":
    main()
