package com.iganapolsky.randomtimer.monetization

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class DisciplinePackCatalogTest {
    @Test
    fun `android pack ids are unique non consumable skus`() {
        val ids = DisciplinePackCatalog.androidProductIds
        assertThat(ids).hasSize(4)
        assertThat(ids.toSet()).hasSize(4)
        ids.forEach { id ->
            assertThat(id).startsWith("pack_")
        }
    }

    @Test
    fun `ios pack ids map one to one with android`() {
        DisciplinePackCatalog.androidProductIds.forEach { androidId ->
            val iosId = DisciplinePackCatalog.iosProductId(androidId)
            assertThat(iosId).startsWith("com.iganapolsky.randomtimer.pack.")
        }
    }

    @Test
    fun `scaffold packs are not required for play verify`() {
        assertThat(DisciplinePackCatalog.androidProductIds).containsNoneOf(
            com.iganapolsky.randomtimer.billing.ProManager.BASE_PRODUCT_ID,
            com.iganapolsky.randomtimer.billing.ProManager.ELITE_PRODUCT_ID,
        )
    }
}
