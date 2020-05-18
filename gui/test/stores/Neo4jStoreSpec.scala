package stores

import org.neo4j.driver.exceptions.ClientException
import org.scalatest.{BeforeAndAfterAll, Matchers, WordSpec}

class Neo4jStoreSpec extends WordSpec with BeforeAndAfterAll with Matchers {
  val sut = new Neo4jStore(new Neo4jStoreConfiguration(password = "nC1aB4mji623s2Zs", uri = "bolt://neo4j:7687", user = "neo4j"))

  override def beforeAll(): Unit = {
    try {
      sut.bootstrap()
    } catch {
      case _: ClientException => // Ignore constraint already exists
    }
    sut.clear()
    sut.putNodes(TestData.nodes)
    sut.putEdges(TestData.edges)
  }

  "The neo4j store" can {
    "get edges by subject" in {
      val node = TestData.nodes(0)
      val edges = sut.getEdgesBySubject(node.id)
      edges should not be empty
      for (edge <- edges) {
        edge.subject should equal(node.id)
      }
    }

    "get a node by ID" in {
      val expected = TestData.nodes(0)
      val actual = sut.getNodeById(expected.id)
      actual should equal(expected)
    }
  }
}