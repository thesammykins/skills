// Native macOS Vision proposals, not an assertion that a face is a webcam.
import Foundation
import ImageIO
import Vision

func box(_ r: CGRect, _ width: Int, _ height: Int) -> [Int] {
    // Vision uses a bottom-left origin; edit plans use top-left pixels.
    return [Int((r.minX * Double(width)).rounded()),
            Int(((1 - r.maxY) * Double(height)).rounded()),
            Int((r.width * Double(width)).rounded()),
            Int((r.height * Double(height)).rounded())]
}

do {
    var rows: [[String: Any]] = []
    let ocr = CommandLine.arguments.contains("--ocr")
    for path in CommandLine.arguments.dropFirst().filter({ $0 != "--ocr" }) {
        let url = URL(fileURLWithPath: path)
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
            throw NSError(domain: "LayoutDetection", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "Cannot read \(path)"])
        }
        if ocr {
            let text = VNRecognizeTextRequest()
            text.revision = VNRecognizeTextRequestRevision3
            text.recognitionLevel = .accurate
            text.recognitionLanguages = ["en-US"]
            text.usesLanguageCorrection = false
            text.usesCPUOnly = true
            try VNImageRequestHandler(cgImage: image).perform([text])
            rows.append(["path": path, "width": image.width, "height": image.height,
                         "text": (text.results ?? []).compactMap { observation -> [String: Any]? in
                guard let candidate = observation.topCandidates(1).first else { return nil }
                return ["text": candidate.string, "confidence": Double(candidate.confidence),
                        "box": box(observation.boundingBox, image.width, image.height)]
            }])
            continue
        }
        let faces = VNDetectFaceRectanglesRequest()
        faces.revision = VNDetectFaceRectanglesRequestRevision3
        faces.usesCPUOnly = true
        let rectangles = VNDetectRectanglesRequest()
        rectangles.revision = VNDetectRectanglesRequestRevision1
        rectangles.usesCPUOnly = true
        rectangles.minimumSize = 0.04
        rectangles.minimumAspectRatio = 0.2
        rectangles.maximumAspectRatio = 1.0
        rectangles.maximumObservations = 64
        rectangles.minimumConfidence = 0.5
        rectangles.quadratureTolerance = 20
        try VNImageRequestHandler(cgImage: image).perform([faces, rectangles])
        rows.append([
            "path": path, "width": image.width, "height": image.height,
            "faces": (faces.results ?? []).map {
                ["box": box($0.boundingBox, image.width, image.height),
                 "confidence": Double($0.confidence)] as [String: Any]
            },
            "rectangles": (rectangles.results ?? []).map {
                ["box": box($0.boundingBox, image.width, image.height),
                 "confidence": Double($0.confidence)] as [String: Any]
            }
        ])
    }
    let data = try JSONSerialization.data(withJSONObject: rows, options: [.sortedKeys])
    FileHandle.standardOutput.write(data)
} catch {
    FileHandle.standardError.write(Data("Layout detection failed: \(error)\n".utf8))
    exit(1)
}
