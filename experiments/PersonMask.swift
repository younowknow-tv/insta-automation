// Per-frame person mattes via Apple's Vision framework.
//
//   swiftc -O PersonMask.swift -o personmask
//   ./personmask <in-dir-of-pngs> <out-dir>
//
// Runs locally, no model download, and it is trained for people specifically,
// which is what this clip is: two people at a table. Writes an 8-bit grayscale
// PNG per input frame, same size as the input.
import Foundation
import Vision
import CoreImage
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("usage: personmask <in-dir> <out-dir>\n".data(using: .utf8)!)
    exit(1)
}
let inDir = URL(fileURLWithPath: args[1])
let outDir = URL(fileURLWithPath: args[2])
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

let files = (try! FileManager.default.contentsOfDirectory(atPath: inDir.path))
    .filter { $0.hasSuffix(".png") }.sorted()

let ciContext = CIContext(options: [.useSoftwareRenderer: false])
var done = 0

for name in files {
    let url = inDir.appendingPathComponent(name)
    guard let img = NSImage(contentsOf: url),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        FileHandle.standardError.write("skip \(name)\n".data(using: .utf8)!); continue
    }

    let req = VNGeneratePersonSegmentationRequest()
    req.qualityLevel = .accurate
    req.outputPixelFormat = kCVPixelFormatType_OneComponent8

    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    try! handler.perform([req])
    guard let mask = (req.results?.first)?.pixelBuffer else {
        FileHandle.standardError.write("no mask \(name)\n".data(using: .utf8)!); continue
    }

    // Vision returns the matte at its own working size; scale it back up to
    // the frame so ffmpeg can use it as an alpha channel directly.
    var ci = CIImage(cvPixelBuffer: mask)
    let sx = CGFloat(cg.width) / ci.extent.width
    let sy = CGFloat(cg.height) / ci.extent.height
    ci = ci.transformed(by: CGAffineTransform(scaleX: sx, y: sy))

    let rect = CGRect(x: 0, y: 0, width: cg.width, height: cg.height)
    guard let outCG = ciContext.createCGImage(ci, from: rect) else { continue }
    let rep = NSBitmapImageRep(cgImage: outCG)
    let png = rep.representation(using: .png, properties: [:])!
    try! png.write(to: outDir.appendingPathComponent(name))
    done += 1
}
print("masked \(done)/\(files.count)")
