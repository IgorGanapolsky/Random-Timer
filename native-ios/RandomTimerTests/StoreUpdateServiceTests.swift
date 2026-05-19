import XCTest
@testable import RandomTimer

final class StoreUpdateServiceTests: XCTestCase {
    func testReturnsNilWhenStoreVersionIsNotNewer() async {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        let session = URLSession(configuration: config)

        MockURLProtocol.requestHandler = { request in
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            let body = """
            {"resultCount":1,"results":[{"version":"1.0.0"}]}
            """
            return (response, Data(body.utf8))
        }

        let service = StoreUpdateService(session: session)
        let result = await service.checkForUpdates(currentVersion: "2.0.0")
        XCTAssertNil(result)
    }

    func testReturnsStoreVersionWhenNewer() async {
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        let session = URLSession(configuration: config)

        MockURLProtocol.requestHandler = { request in
            let response = HTTPURLResponse(
                url: request.url!,
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            let body = """
            {"resultCount":1,"results":[{"version":"2.0.0"}]}
            """
            return (response, Data(body.utf8))
        }

        let service = StoreUpdateService(session: session)
        let result = await service.checkForUpdates(currentVersion: "1.0.0")
        XCTAssertEqual(result, "2.0.0")
    }
}

private final class MockURLProtocol: URLProtocol {
    static var requestHandler: ((URLRequest) throws -> (HTTPURLResponse, Data))?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        guard let handler = MockURLProtocol.requestHandler else {
            client?.urlProtocol(self, didFailWithError: URLError(.badURL))
            return
        }
        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}
