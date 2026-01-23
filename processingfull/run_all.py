"""
Run All Scripts
Convenience script to run the complete workflow in sequence.
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """Run a Python script and handle errors."""
    print("\n" + "=" * 70)
    print(f"🚀 {description}")
    print("=" * 70)
    
    if not os.path.exists(script_name):
        print(f"❌ Error: {script_name} not found!")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️  {description} interrupted by user")
        return False


def main():
    """Run all scripts in sequence."""
    print("=" * 70)
    print("🏨 Hotel Room Classification - Complete Workflow")
    print("=" * 70)
    
    scripts = [
        ("run_ml_model.py", "Training model and generating predictions"),
        ("evaluate.py", "Evaluating model performance"),
        ("error_analysis.py", "Analyzing error patterns")
    ]
    
    # Check if required files exist
    required_files = ["train.csv"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"\n❌ Missing required files: {', '.join(missing_files)}")
        print("Please ensure train.csv exists in the project directory.")
        return
    
    # Run scripts in sequence
    success_count = 0
    for script, description in scripts:
        if run_script(script, description):
            success_count += 1
        else:
            print(f"\n⚠️  Stopping workflow due to error in {script}")
            break
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Workflow Summary")
    print("=" * 70)
    print(f"✅ Completed: {success_count}/{len(scripts)} steps")
    
    if success_count == len(scripts):
        print("\n🎉 All steps completed successfully!")
        print("\nGenerated files:")
        output_files = [
            "room_class_model.pkl",
            "train_with_prediction.csv",
            "val_with_prediction.csv",
            "val_with_error_analysis.csv"
        ]
        for file in output_files:
            if os.path.exists(file):
                print(f"  ✅ {file}")
            else:
                print(f"  ⚠️  {file} (not found)")
    else:
        print("\n⚠️  Workflow incomplete. Please check errors above.")


if __name__ == "__main__":
    main()
