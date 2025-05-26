import assert from "assert";
import { 
  TestHelpers,
  AlgebraFactory_CustomPool
} from "generated";
const { MockDb, AlgebraFactory } = TestHelpers;

describe("AlgebraFactory contract CustomPool event tests", () => {
  // Create mock db
  const mockDb = MockDb.createMockDb();

  // Creating mock for AlgebraFactory contract CustomPool event
  const event = AlgebraFactory.CustomPool.createMockEvent({/* It mocks event fields with default values. You can overwrite them if you need */});

  it("AlgebraFactory_CustomPool is created correctly", async () => {
    // Processing the event
    const mockDbUpdated = await AlgebraFactory.CustomPool.processEvent({
      event,
      mockDb,
    });

    // Getting the actual entity from the mock database
    let actualAlgebraFactoryCustomPool = mockDbUpdated.entities.AlgebraFactory_CustomPool.get(
      `${event.chainId}_${event.block.number}_${event.logIndex}`
    );

    // Creating the expected entity
    const expectedAlgebraFactoryCustomPool: AlgebraFactory_CustomPool = {
      id: `${event.chainId}_${event.block.number}_${event.logIndex}`,
      deployer: event.params.deployer,
      token0: event.params.token0,
      token1: event.params.token1,
      pool: event.params.pool,
    };
    // Asserting that the entity in the mock database is the same as the expected entity
    assert.deepEqual(actualAlgebraFactoryCustomPool, expectedAlgebraFactoryCustomPool, "Actual AlgebraFactoryCustomPool should be the same as the expectedAlgebraFactoryCustomPool");
  });
});
