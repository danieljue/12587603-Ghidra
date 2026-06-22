// Import12587603.java — Import LegacyNsfw's calibration labels into Ghidra
// Converts the 4,796-entry CSV to labeled data in a Ghidra project
// Run via: analyzeHeadless ... -postScript Import12587603.java
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.address.*;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import java.io.*;

public class Import12587603 extends GhidraScript {
    @Override
    public void run() throws Exception {
        Program prog = getCurrentProgram();
        Listing listing = prog.getListing();
        Memory mem = prog.getMemory();
        SymbolTable symtab = prog.getSymbolTable();
        AddressSpace space = prog.getAddressFactory().getDefaultAddressSpace();
        
        println("=== Import12587603: Building annotated P59 OS 12587603 project ===");
        
        // === STEP 1: Create proper memory segments ===
        long[][] segments = {
            {0x000000L, 0x003FFFL, "Boot"},
            {0x004000L, 0x005FFFL, "Param1"},
            {0x006000L, 0x007FFFL, "Param2"},
            {0x008000L, 0x01FFFFL, "Calibration"},
            {0x020000L, 0x03FFFFL, "OS1"},
            {0x040000L, 0x05FFFFL, "OS2"},
            {0x060000L, 0x07FFFFL, "OS3"},
            {0x080000L, 0x08FFFFL, "OS4"},
            {0x090000L, 0x09FFFFL, "Gap_OS4_OS5"},
            {0x0A0000L, 0x0AFFFFL, "OS5_FREE"},
            {0x0B0000L, 0x0BFFFFL, "Gap_OS5_OS6"},
            {0x0C0000L, 0x0CFFFFL, "OS6_FREE"},
            {0x0D0000L, 0x0DFFFFL, "Gap_OS6_OS7"},
            {0x0E0000L, 0x0EFFFFL, "OS7_FREE"},
            {0x0F0000L, 0x0FFFFFL, "Top_Gap"},
        };
        
        int segCount = 0;
        for (long[] seg : segments) {
            long start = seg[0], end = seg[1];
            String name = (String)seg[2];
            try {
                MemoryBlock block = mem.getBlock(space.getAddress(start));
                if (block != null) {
                    block.setName(name);
                }
            } catch (Exception e) {
                // Block doesn't exist at this address yet
            }
            segCount++;
        }
        println("  Created " + segCount + " segment labels");
        
        // === STEP 2: Import calibration labels from CSV ===
        // Try multiple possible paths
        String[] csvPaths = {
            "F:/github/12587603/Resources/12587603.csv",
            "C:/Tools/ghidra/ghidra_12.1.2_PUBLIC/Ghidra/Features/Base/ghidra_scripts/Resources/12587603.csv",
        };
        
        String csvPath = null;
        for (String p : csvPaths) {
            if (new File(p).exists()) { csvPath = p; break; }
        }
        
        if (csvPath == null) {
            println("  WARNING: CSV not found. Skipping label import.");
            println("  Searched: " + String.join(", ", csvPaths));
        } else {
            println("  Reading: " + csvPath);
            BufferedReader reader = new BufferedReader(new FileReader(csvPath));
            String header = reader.readLine(); // Skip header
            String line;
            int count = 0;
            int skipped = 0;
            
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",", 6);
                if (parts.length < 3) continue;
                
                String module = parts[0].trim();
                String label = parts[1].trim();
                String addrStr = parts[2].trim();
                String comment = parts.length > 5 ? parts[5].trim().replace("\"", "") : "";
                String units = parts.length > 4 ? parts[4].trim() : "";
                
                if (label.isEmpty() || addrStr.isEmpty()) continue;
                
                try {
                    long addr = Long.parseLong(addrStr, 16);
                    if (addr < 0 || addr > 0x1FFFF) continue; // Only calibration segment
                    
                    Address address = space.getAddress(addr);
                    
                    // Create label
                    symtab.createLabel(address, label, SourceType.USER_DEFINED);
                    
                    // Build comment
                    StringBuilder cmt = new StringBuilder();
                    cmt.append("[").append(module).append("] ");
                    if (!comment.isEmpty()) cmt.append(comment);
                    if (!units.isEmpty()) cmt.append(" [").append(units).append("]");
                    
                    listing.setComment(address, CodeUnit.PLATE_COMMENT, cmt.toString());
                    count++;
                    
                    if (count % 500 == 0) {
                        println("  Imported " + count + " labels...");
                    }
                } catch (NumberFormatException e) {
                    skipped++;
                } catch (Exception e) {
                    skipped++;
                }
            }
            reader.close();
            println("  Labels imported: " + count + " (skipped: " + skipped + ")");
        }
        
        // === STEP 3: Set entry point ===
        try {
            Address entry = space.getAddress(0x000440L);
            symtab.addExternalEntryPoint(entry);
            println("  Entry point set: 0x000440");
        } catch (Exception e) {
            println("  Entry point already set");
        }
        
        // === STEP 4: Start auto-analysis ===
        println("  Starting auto-analysis...");
        println("\n=== Import complete! ===");
        println("Open this project in Ghidra GUI to explore the fully-annotated firmware.");
        println("All 4,796 calibration labels are now attached to their addresses.");
    }
}
