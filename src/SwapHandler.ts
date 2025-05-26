import { AlgebraPool_Swap } from "generated";

import { AlgebraPool } from "generated";

AlgebraPool.Swap.handler(async ({ event, context }) => {
	const entity: AlgebraPool_Swap = {
		id: `${event.chainId}_${event.block.number}_${event.logIndex}`,
		tx: event.transaction.hash,
		blockNumber: event.block.number,
		sender: event.transaction.from as string,
		amount0: event.params.amount0,
		amount1: event.params.amount1,
		price: event.params.price,
		liquidity: event.params.liquidity,
	};

	context.AlgebraPool_Swap.set(entity);
});
