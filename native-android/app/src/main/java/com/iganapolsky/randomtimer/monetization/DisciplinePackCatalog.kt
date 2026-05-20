package com.iganapolsky.randomtimer.monetization

/**
 * P2 scaffold: non-consumable discipline IAP packs (not yet in Play / App Store catalogs).
 * Create products in console before enabling billing queries.
 */
object DisciplinePackCatalog {
    const val PACK_SPECIAL_FORCES = "pack_special_forces"
    const val PACK_BOXING_HIIT = "pack_boxing_hiit"
    const val PACK_CROSSFIT = "pack_crossfit"
    const val PACK_BJJ = "pack_bjj"

    val androidProductIds: List<String> =
        listOf(
            PACK_SPECIAL_FORCES,
            PACK_BOXING_HIIT,
            PACK_CROSSFIT,
            PACK_BJJ,
        )

    private val iosByAndroid: Map<String, String> =
        mapOf(
            PACK_SPECIAL_FORCES to "com.iganapolsky.randomtimer.pack.special_forces",
            PACK_BOXING_HIIT to "com.iganapolsky.randomtimer.pack.boxing_hiit",
            PACK_CROSSFIT to "com.iganapolsky.randomtimer.pack.crossfit",
            PACK_BJJ to "com.iganapolsky.randomtimer.pack.bjj",
        )

    fun iosProductId(androidProductId: String): String =
        iosByAndroid[androidProductId]
            ?: error("Unknown discipline pack: $androidProductId")

    val iosProductIds: List<String> = androidProductIds.map(::iosProductId)
}
