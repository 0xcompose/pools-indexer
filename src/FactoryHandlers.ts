import { AlgebraFactory_Pool } from "generated";

import { AlgebraFactory } from "generated";

AlgebraFactory.Pool.handler(async ({ event, context }) => {
	const entity: AlgebraFactory_Pool = {
		id: `${event.chainId}_${event.block.number}_${event.logIndex}`,
		token0: event.params.token0,
		token1: event.params.token1,
		pool: event.params.pool,
	};

	context.AlgebraFactory_Pool.set(entity);
});

AlgebraFactory.Pool.contractRegister(async ({ event, context }) => {
	context.addAlgebraPool(event.params.pool);
});
