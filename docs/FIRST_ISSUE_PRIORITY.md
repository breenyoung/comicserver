# Series API v6 - Prioritize Plain Issues for Volume Covers

## The Problem

**Scenario:** Superboy Volume 1
- Issue #0 (format="Special") - Released later as part of Zero Hour crossover
- Issue #1 (no format) - The actual first issue
- Issue #2, #3, etc. (no format)

### Old Behavior (v5)
```
Volume 1 cover: Uses Issue #0
Because: Sorts by number, 0 < 1
Problem: #0 is a special, not representative of the series
```

### New Behavior (v6)
```
Volume 1 cover: Uses Issue #1
Because: Prioritizes plain issues over specials
Result: Cover shows the true first issue ✓
```

## The Solution

### New Helper Function

```python
def get_first_issue(comics_list: List[Comic]) -> Comic:
    """
    Get the first issue from a list of comics, prioritizing plain issues.
    
    Returns the earliest plain issue by number, or if no plain issues exist,
    returns the earliest issue overall.
    """
    if not comics_list:
        return None
    
    # Sort all comics by issue number
    sorted_comics = sorted(
        comics_list, 
        key=lambda c: float(c.number) if c.number else 0
    )
    
    # Try to find the first plain issue
    plain_comics = [c for c in sorted_comics if is_plain_issue(c)]
    
    if plain_comics:
        # Return earliest plain issue
        return plain_comics[0]
    else:
        # No plain issues, return earliest overall
        return sorted_comics[0]
```

### Volume Cover Selection

```python
# OLD (v5)
sorted_comics = sorted(volume_comics, key=lambda c: float(c.number))
first_issue = sorted_comics[0]  # Just picks #0

# NEW (v6)
first_issue = get_first_issue(volume_comics)  # Picks first plain issue
```

### Series Cover Selection

```python
# OLD (v5)
sorted_comics = sort_by_volume_and_number(comics)
first_issue = sorted_comics[0]  # Just picks earliest by number

# NEW (v6)
sorted_comics = sort_by_volume_and_number(comics)
plain_comics = [c for c in sorted_comics if is_plain_issue(c)]
first_issue = plain_comics[0] if plain_comics else sorted_comics[0]
```

## Examples

### Example 1: Superboy Volume 1

**Comics:**
- #0 (format="Special") - Zero Hour tie-in
- #1 (no format) - First regular issue
- #2-#100 (no format)

**v5 Behavior:**
```
Volume cover: Issue #0 ❌
Series cover: Issue #0 ❌
```

**v6 Behavior:**
```
Volume cover: Issue #1 ✅
Series cover: Issue #1 ✅
```

---

### Example 2: Batman Volume 2 (New 52)

**Comics:**
- #0 (format="Special") - Origin retelling
- #1 (no format) - First issue
- #2-#52 (no format)
- Annual #1 (format="Annual")

**v6 Behavior:**
```
Volume cover: Issue #1 ✅ (skips #0)
Series cover: Issue #1 ✅ (skips #0)
```

---

### Example 3: Standalone Graphic Novel

**Comics:**
- #1 (format="Graphic Novel")

**v6 Behavior:**
```
Volume cover: Issue #1 ✅ (only option)
Series cover: Issue #1 ✅ (only option)
```

*Falls back to earliest issue when no plain issues exist*

---

### Example 4: Mini-Series with Special #0

**Comics:**
- #0 (format="One-Shot") - Prequel
- #1-#4 (no format) - Main story

**v6 Behavior:**
```
Volume cover: Issue #1 ✅ (skips #0)
Series cover: Issue #1 ✅ (skips #0)
```

## Logic Flow

```
For each volume:
  1. Get all comics in volume
  2. Sort by issue number
  3. Filter to plain issues only
  4. If plain issues exist:
     → Use earliest plain issue as cover
  5. Else (no plain issues):
     → Use earliest issue overall as cover

For series overall:
  1. Get all comics across all volumes
  2. Sort by volume number, then issue number
  3. Filter to plain issues only
  4. If plain issues exist:
     → Use earliest plain issue as cover
  5. Else (no plain issues):
     → Use earliest issue overall as cover
```

## Benefits

✅ **Accurate representation** - Volume covers show the true first issue  
✅ **Handles #0 issues** - Common in crossovers, correctly skipped  
✅ **Handles specials** - One-shots, prequels don't become covers  
✅ **Graceful fallback** - Works for standalone series with only specials  
✅ **Consistent logic** - Same prioritization for volumes and series  

## Edge Cases Handled

### Case 1: Only Special Issues
```
Volume 1: All issues are specials
Result: Uses earliest special as cover (no other option)
```

### Case 2: Plain Issues Start at #2
```
Volume 1:
- #0 (special)
- #1 (special)
- #2 (plain) ← First plain issue
- #3+ (plain)

Result: Uses #2 as cover ✅
```

### Case 3: Multiple Volumes
```
Volume 1:
- #0 (special)
- #1-#50 (plain)

Volume 2:
- #1-#25 (plain)

Series cover: Vol 1, #1 ✅
Volume 1 cover: Vol 1, #1 ✅
Volume 2 cover: Vol 2, #1 ✅
```

## Installation

Replace your series API:

```bash
cp series_api_v6.py /path/to/your-project/app/api/series.py
python main.py  # Restart
```

## Testing

After updating, verify:

1. **Series with #0 special**: Cover should be #1, not #0
2. **Volume with #0 special**: Volume cover should be #1, not #0
3. **Standalone graphic novel**: Should still use the graphic novel as cover
4. **Normal series without specials**: Should work exactly as before

## What Changed from v5

- **Added:** `get_first_issue()` helper function
- **Changed:** Volume cover selection logic
- **Changed:** Series cover selection logic
- **Result:** Plain issues prioritized for all covers

## Download

- [series_api_v6.py](computer:///mnt/user-data/outputs/series_api_v6.py)

---

**Covers now represent the actual first issue!** 🎯
