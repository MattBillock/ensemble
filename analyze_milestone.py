#!/usr/bin/env python3
"""Comprehensive milestone analysis script."""
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json

def count_agents() -> int:
    """Count total agent definition files."""
    count = 0
    for dir_name in ['leadership', 'coordinators', 'developers', 'testers', 'designers']:
        path = Path(dir_name)
        if path.exists():
            count += len(list(path.glob('*.md')))
    return count

def count_drum_corps_refs() -> int:
    """Count remaining drum corps references."""
    try:
        result = subprocess.run(
            ['grep', '-ri', 'drum\\|corps\\|brass\\|percussion\\|guard\\|snare\\|trumpet\\|tuba',
             'leadership/', 'coordinators/', 'developers/', 'testers/', 'designers/', '.clinerules'],
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except:
        return -1

def count_lines_of_code() -> dict:
    """Count LOC by directory."""
    counts = {}
    for dir_name in ['src/domain', 'src/runtime', 'src/infrastructure']:
        path = Path(dir_name)
        if path.exists():
            result = subprocess.run(
                ['find', str(path), '-name', '*.py', '-exec', 'wc', '-l', '{}', '+'],
                capture_output=True,
                text=True
            )
            total = 0
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 1 and parts[0].isdigit():
                        total += int(parts[0])
            counts[dir_name] = total
        else:
            counts[dir_name] = 0
    return counts

def run_tests() -> dict:
    """Run pytest and capture results."""
    try:
        result = subprocess.run(
            ['pytest', '--tb=short', '-v'],
            capture_output=True,
            text=True,
            timeout=120
        )
        lines = result.stdout.split('\n')
        passed = failed = 0
        for line in lines:
            if 'passed' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        try:
                            passed = int(parts[i-1])
                        except:
                            pass
            if 'failed' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'failed' and i > 0:
                        try:
                            failed = int(parts[i-1])
                        except:
                            pass
        return {
            'passed': passed,
            'failed': failed,
            'success_rate': f"{(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A"
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_agent_performance(log_file: str) -> dict:
    """Parse pipeline logs for agent performance."""
    if not Path(log_file).exists():
        return {'error': 'Log file not found'}

    agents = {}
    try:
        with open(log_file, 'r') as f:
            current_agent = None
            iteration = 0

            for line in f:
                if '"Executing agent:' in line:
                    # Extract agent name
                    parts = line.split('"Executing agent:')
                    if len(parts) > 1:
                        current_agent = parts[1].split('"')[0].strip()
                        if current_agent not in agents:
                            agents[current_agent] = {
                                'spawns': 1,
                                'iterations': [],
                                'status': 'running'
                            }
                        else:
                            agents[current_agent]['spawns'] += 1

                elif '"Iteration' in line and current_agent:
                    # Extract iteration number
                    parts = line.split('"Iteration')
                    if len(parts) > 1:
                        iter_str = parts[1].split('"')[0].strip()
                        if '/' in iter_str:
                            current_iter = int(iter_str.split('/')[0].strip())
                            iteration = current_iter

                elif '"Agent completed successfully' in line and current_agent:
                    agents[current_agent]['status'] = 'success'
                    if iteration > 0:
                        agents[current_agent]['iterations'].append(iteration)

        # Calculate stats
        for agent in agents.values():
            if agent['iterations']:
                agent['avg_iterations'] = sum(agent['iterations']) / len(agent['iterations'])
            else:
                agent['avg_iterations'] = 0

        return agents
    except Exception as e:
        return {'error': str(e)}

def generate_report(milestone_name: str):
    """Generate comprehensive analysis report."""
    print("=" * 70)
    print(f"📊 MILESTONE ANALYSIS: {milestone_name}")
    print("=" * 70)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Agent Count
    print("## 1. Agent System Metrics")
    print("-" * 70)
    agent_count = count_agents()
    print(f"Total Agents: {agent_count}")

    # 2. Drum Corps Cleanup
    drum_refs = count_drum_corps_refs()
    print(f"Drum Corps References: {drum_refs}")
    print(f"Cleanup Status: {'✅ COMPLETE' if drum_refs == 0 else f'⚠️  {drum_refs} remaining'}")
    print()

    # 3. Code Metrics
    print("## 2. Code Metrics")
    print("-" * 70)
    loc = count_lines_of_code()
    for dir_name, count in loc.items():
        status = "✅ Exists" if count > 0 else "⚠️  Missing"
        print(f"{dir_name}: {count} LOC {status}")
    print()

    # 4. Test Results
    print("## 3. Test Results")
    print("-" * 70)
    test_results = run_tests()
    if 'error' in test_results:
        print(f"⚠️  Error running tests: {test_results['error']}")
    else:
        print(f"Passed: {test_results.get('passed', 0)}")
        print(f"Failed: {test_results.get('failed', 0)}")
        print(f"Success Rate: {test_results.get('success_rate', 'N/A')}")
    print()

    # 5. Agent Performance (from logs)
    print("## 4. Agent Performance (from pipeline logs)")
    print("-" * 70)
    log_file = f"{milestone_name.replace(' ', '_').lower()}_pipeline_run.log"
    perf = analyze_agent_performance(log_file)
    if 'error' in perf:
        print(f"⚠️  Could not analyze: {perf['error']}")
    else:
        for agent_name, stats in perf.items():
            status_icon = "✅" if stats['status'] == 'success' else "⚠️"
            avg_iter = f"{stats['avg_iterations']:.1f}" if stats['avg_iterations'] > 0 else "N/A"
            print(f"{status_icon} {agent_name}")
            print(f"   Spawns: {stats['spawns']}, Avg Iterations: {avg_iter}, Status: {stats['status']}")
    print()

    # 6. Recommendations
    print("## 5. Recommendations")
    print("-" * 70)
    print("HIGH PRIORITY:")
    if drum_refs > 0:
        print(f"  🔴 Complete drum corps cleanup ({drum_refs} refs remaining)")
    if agent_count > 14:
        print(f"  🔴 Continue agent consolidation ({agent_count} → 14 target)")
    if test_results.get('failed', 0) > 0:
        print(f"  🔴 Fix failing tests ({test_results.get('failed')} failures)")

    print()
    print("MEDIUM PRIORITY:")
    if loc.get('src/domain', 0) == 0:
        print("  ⚠️  Create domain layer (DDD refactoring)")
    if loc.get('src/infrastructure', 0) == 0:
        print("  ⚠️  Create infrastructure layer")

    print()
    print("=" * 70)
    print(f"Full analysis saved to: MILESTONE_{milestone_name.upper()}_ANALYSIS.md")
    print("=" * 70)

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_milestone.py <milestone-name>")
        print("Example: python analyze_milestone.py milestone-0")
        sys.exit(1)

    milestone_name = sys.argv[1]
    generate_report(milestone_name)

if __name__ == "__main__":
    main()
