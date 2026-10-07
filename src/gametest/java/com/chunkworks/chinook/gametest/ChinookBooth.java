/*
 * The Chinook - a Boeing CH-47 for Rotorcraft.
 * Copyright (C) 2026 Rusty Shackleford and nfx
 *
 * This program is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
 * for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */
package com.chunkworks.chinook.gametest;

import com.chunkworks.rotorcraft.Aircraft;
import com.chunkworks.rotorcraft.RotorcraftContent;
import com.chunkworks.rotorcraft.SlungLoad;
import com.chunkworks.rotorcraft.client.RotorcraftKeys;
import com.chunkworks.rotorcraft.domain.FlightInput;
import com.chunkworks.vanillawheels.Vehicle;
import com.mojang.blaze3d.platform.NativeImage;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.IntPredicate;
import java.util.function.Supplier;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameRules;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.phys.Vec3;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The Chinook on film, in a flat world at noon: parked, from the front quarter, the left side and the
 * rear quarter; dyed red; its ramp lowered with three cows aboard; the nose close up; twelve aboard,
 * seen through the ramp; the pilot's own view; hovering with its rotors spun up, seen from the
 * ground; the Sling Container hanging under it; and the crop sprayer over a wheat field, flown by the
 * booth's own player with the keys held, seen from behind. One {@code booth: PASS} or
 * {@code booth: FAIL} line per check; the Gradle task reads them. Client only, active only under
 * {@code chinook.photobooth}.
 */
@EventBusSubscriber(modid = GameTestMod.MOD_ID, value = Dist.CLIENT)
public final class ChinookBooth {
    private ChinookBooth() {}

    private static final Logger LOG = LoggerFactory.getLogger("Chinook booth");
    private static final boolean ACTIVE = Boolean.getBoolean("chinook.photobooth");
    private static final ResourceLocation CHINOOK = ResourceLocation.fromNamespaceAndPath("chinook", "chinook");
    private static final ResourceLocation CONTAINER = ResourceLocation.fromNamespaceAndPath("rotorcraft", "sling_container");

    private enum Phase { TITLE, LOADING, PLACING, RUNNING, DONE }

    private record Step(int at, Runnable action) {}

    private static final int HOLD = 100;
    private static final int SETTLE = 60;
    /** Where the Chinook stands (its middle), facing east; the field lies east of it. */
    private static final double HX = 0.5;
    private static final double HZ = 30.5;
    private static final float EAST = -90.0f;

    private static boolean muted = false;
    private static Phase phase = Phase.TITLE;
    private static int tick = 0;
    private static List<Step> steps;
    private static UUID chinook;
    private static UUID box;
    private static double ground;

    @SubscribeEvent
    public static void onClientTick(ClientTickEvent.Post event) {
        if (!ACTIVE) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        if (!muted) {
            // Silent from the first tick, before the title music: Rusty listens to music while these run.
            mc.options.getSoundSourceOptionInstance(net.minecraft.sounds.SoundSource.MASTER).set(0.0);
            muted = true;
        }
        switch (phase) {
            case TITLE -> {
                if (mc.screen instanceof TitleScreen && mc.getOverlay() == null) {
                    phase = Phase.LOADING;
                    createWorld(mc);
                }
            }
            case LOADING -> {
                MinecraftServer server = mc.getSingleplayerServer();
                if (mc.level != null && mc.player != null && mc.screen == null && server != null
                        && mc.level.hasChunkAt(mc.player.blockPosition())) {
                    phase = Phase.PLACING;
                    mc.options.hideGui = true;
                    steps = plan(mc);
                    onServer(mc, ChinookBooth::setUp);
                }
            }
            case PLACING -> {
                if (mc.player != null && client(mc, chinook) != null) {
                    phase = Phase.RUNNING;
                    tick = 0;
                }
            }
            case RUNNING -> {
                for (Step step : steps) {
                    if (step.at() == tick) {
                        step.action().run();
                    }
                }
                tick++;
            }
            case DONE -> { }
        }
    }

    private static void createWorld(Minecraft mc) {
        GameRules rules = new GameRules();
        rules.getRule(GameRules.RULE_WEATHER_CYCLE).set(false, null);
        rules.getRule(GameRules.RULE_DAYLIGHT).set(false, null);
        rules.getRule(GameRules.RULE_DOMOBSPAWNING).set(false, null);
        rules.getRule(GameRules.RULE_RANDOMTICKING).set(0, null);
        LevelSettings settings = new LevelSettings("Chinook booth", GameType.CREATIVE, false, Difficulty.PEACEFUL,
                true, rules, WorldDataConfiguration.DEFAULT);
        WorldOptions options = new WorldOptions(1L, false, false);
        mc.createWorldOpenFlows().createFreshLevel("chinook-booth", settings, options,
                registries -> registries.registryOrThrow(Registries.WORLD_PRESET).getHolderOrThrow(WorldPresets.FLAT)
                        .value().createWorldDimensions(),
                mc.screen);
    }

    /** Noon; the Chinook parked facing east; a wheat field laid east of it for the sprayer. */
    private static void setUp(ServerPlayer sp) {
        ServerLevel level = sp.serverLevel();
        level.setDayTime(6000L);
        ground = level.getMinBuildHeight() + 4;
        sp.getAbilities().flying = true;
        sp.onUpdateAbilities();
        sp.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        sp.teleportTo(level, HX + 9, ground + 3, HZ - 12, 30.0f, 10.0f);
        // A field of young wheat, 20 by 14, from 14 blocks east of the mast.
        for (int x = 14; x < 34; x++) {
            for (int z = -7; z < 7; z++) {
                BlockPos soil = BlockPos.containing(HX + x, ground - 1, HZ + z);
                level.setBlockAndUpdate(soil, Blocks.FARMLAND.defaultBlockState());
                level.setBlockAndUpdate(soil.above(), Blocks.WHEAT.defaultBlockState());
            }
        }
        chinook = spawnChinook(level).getUUID();
    }

    private static Aircraft spawnChinook(ServerLevel level) {
        Vehicle v = Vehicle.create(level, CHINOOK, new Vec3(HX, ground, HZ), EAST);
        if (!(v instanceof Aircraft a)) {
            LOG.error("booth: FAIL the Chinook is an aircraft -- {}", v);
            throw new IllegalStateException("no Chinook");
        }
        a.setFuel(a.tank().capacity());
        level.addFreshEntity(a);
        return a;
    }

    /** effects: puts the booth's player at {@code from}, looking at {@code at} */
    private static void aim(ServerPlayer sp, Vec3 from, Vec3 at) {
        Vec3 d = at.subtract(from);
        float yaw = (float) Math.toDegrees(Math.atan2(-d.x, d.z));
        float pitch = (float) -Math.toDegrees(Math.atan2(d.y, Math.hypot(d.x, d.z)));
        sp.teleportTo(sp.serverLevel(), from.x, from.y - sp.getEyeHeight(), from.z, yaw, pitch);
    }

    /** effects: returns the middle of the Chinook's hull, two blocks up: where a camera aims (its origin is the middle) */
    private static Vec3 middle(Aircraft a) {
        return a.position().add(0.0, 2.0, 0.0);
    }

    /** effects: aims the booth's player from {@code offset} (blocks, the world's axes) off the Chinook's middle at it */
    private static void shot(ServerPlayer sp, double dx, double dy, double dz) {
        withChinook(sp, a -> {
            Vec3 m = middle(a);
            aim(sp, m.add(dx, dy, dz), m);
        });
    }

    private static List<Step> plan(Minecraft mc) {
        List<Step> s = new ArrayList<>();
        int t = HOLD;
        // --- parked: the front quarter, the side, the rear quarter --------------------------------
        s.add(new Step(t - SETTLE, () -> onServer(mc, sp -> shot(sp, 12.0, 4.0, -12.0))));
        s.add(new Step(t, () -> {
            int green = count(mc, ChinookBooth::olive);
            shoot(mc, "booth-threequarter");
            verdict("the stock Chinook shows its Army green", () -> green > 20000 ? null : "green pixels " + green);
            onServer(mc, sp -> shot(sp, 0.0, 1.0, -19.0));
        }));
        s.add(new Step(t += SETTLE, () -> {
            shoot(mc, "booth-side");
            onServer(mc, sp -> shot(sp, -14.0, 5.0, 11.0));
        }));
        s.add(new Step(t += SETTLE, () -> {
            shoot(mc, "booth-rear");
            onServer(mc, sp -> {
                withChinook(sp, a -> a.setPaint(DyeColor.RED));
                shot(sp, 12.0, 4.0, -12.0);
            });
        }));
        s.add(new Step(t += SETTLE, () -> {
            int red = count(mc, ChinookBooth::redPaint);
            shoot(mc, "booth-red");
            verdict("dye paints it red", () -> red > 12000 ? null : "red pixels " + red);
            // A fresh one, its ramp lowered, three cows aboard; seen from behind and to the left.
            onServer(mc, sp -> {
                ServerLevel level = sp.serverLevel();
                if (level.getEntity(chinook) instanceof Aircraft old) {
                    old.discard();
                }
                Aircraft a = spawnChinook(level);
                chinook = a.getUUID();
                a.toggleDoors();
                for (int i = 0; i < 3; i++) {
                    var cow = EntityType.COW.create(level);
                    if (cow != null) {
                        cow.setPos(a.getX(), a.getY(), a.getZ());
                        cow.setNoAi(true);
                        level.addFreshEntity(cow);
                        if (!cow.startRiding(a, true)) {
                            LOG.error("booth: FAIL a cow boards the Chinook");
                        }
                    }
                }
                Vec3 tail = a.position().add(a.rotate(new com.chunkworks.vanillawheels.domain.Vec(0.0, 1.4, -6.5)));
                aim(sp, tail.add(-7.5, 2.5, -6.0), tail);
            });
        }));
        s.add(new Step(t += SETTLE, () -> {
            Aircraft a = client(mc, chinook);
            shoot(mc, "booth-ramp");
            verdict("the ramp is down", () -> a != null && a.doorSwing(1.0f) > 0.9f ? null : "swing " + (a == null ? null : a.doorSwing(1.0f)));
            verdict("with three cows aboard", () -> a != null && a.animals().size() == 3 ? null : "animals " + (a == null ? null : a.animals().size()));
            onServer(mc, sp -> withChinook(sp, h -> {
                Vec3 nose = h.position().add(h.rotate(new com.chunkworks.vanillawheels.domain.Vec(0.0, 1.8, 7.0)));
                aim(sp, nose.add(4.5, 1.5, -4.2), nose);
            }));
        }));
        s.add(new Step(t += SETTLE, () -> shoot(mc, "booth-nose")));
        // --- twelve people aboard, seen up the ramp -----------------------------------------------
        s.add(new Step(t += 2, () -> onServer(mc, sp -> {
            ServerLevel level = sp.serverLevel();
            if (level.getEntity(chinook) instanceof Aircraft old) {
                old.ejectPassengers();
                old.discard();
            }
            Aircraft a = spawnChinook(level);
            chinook = a.getUUID();
            a.toggleDoors();
            for (int i = 0; i < 14; i++) {
                ServerPlayer rider = standIn(sp, "rider" + i, a.position());
                if (!rider.startRiding(a, true)) {
                    LOG.error("booth: FAIL rider {} takes a seat", i);
                }
            }
            Vec3 in = a.position().add(a.rotate(new com.chunkworks.vanillawheels.domain.Vec(0.0, 1.7, 0.0)));
            Vec3 at = a.position().add(a.rotate(new com.chunkworks.vanillawheels.domain.Vec(0.4, 2.3, -14.5)));
            aim(sp, at, in);
        })));
        s.add(new Step(t += SETTLE, () -> {
            Aircraft a = client(mc, chinook);
            shoot(mc, "booth-cabin");
            verdict("fourteen aboard", () -> a != null && a.getPassengers().size() == 14 ? null : "passengers " + (a == null ? null : a.getPassengers().size()));
        }));
        // --- the pilot's own view ----------------------------------------------------------------
        s.add(new Step(t += 2, () -> onServer(mc, sp -> withChinook(sp, a -> {
            for (var rider : List.copyOf(a.getPassengers())) {
                rider.stopRiding();
                if (rider instanceof ServerPlayer standIn) {
                    standIn.connection.disconnect(net.minecraft.network.chat.Component.literal("booth"));
                }
            }
            a.toggleDoors();
            sp.getAbilities().flying = false;
            sp.onUpdateAbilities();
            sp.startRiding(a, true);
        }))));
        s.add(new Step(t += 20, () -> {
            if (mc.player != null) {
                mc.player.setYRot(EAST);
                mc.player.setXRot(10.0f);
            }
        }));
        s.add(new Step(t += SETTLE, () -> {
            Aircraft a = client(mc, chinook);
            shoot(mc, "booth-cockpit");
            verdict("the booth's player flies it from the pilot's seat", () -> a != null && a.getControllingPassenger() == mc.player ? null : "pilot " + (a == null ? null : a.getControllingPassenger()));
        }));
        // --- hovering seven up, rotors spun, seen from the ground ---------------------------------
        s.add(new Step(t += 2, () -> onServer(mc, sp -> {
            sp.stopRiding();
            sp.getAbilities().flying = true;
            sp.onUpdateAbilities();
            withChinook(sp, a -> {
                ArmorStand stand = EntityType.ARMOR_STAND.create(sp.serverLevel());
                if (stand != null) {
                    stand.setInvisible(true);
                    stand.setPos(a.getX(), a.getY(), a.getZ());
                    sp.serverLevel().addFreshEntity(stand);
                    stand.startRiding(a, true);
                }
                a.setScriptedFlight(new FlightInput(0, 0, 1, true, false, 0.0));
            });
        })));
        s.add(new Step(t += 100, () -> onServer(mc, sp -> withChinook(sp, a -> {
            a.setScriptedFlight(new FlightInput(0, 0, 0, true, false, 0.0));
            a.setPos(a.getX(), ground + 7.0, a.getZ());
        }))));
        s.add(new Step(t += 30, () -> onServer(mc, sp -> withChinook(sp, a -> aim(sp, middle(a).add(9.0, -6.0, -19.0), middle(a).add(0.0, 1.0, 0.0))))));
        s.add(new Step(t += SETTLE, () -> {
            Aircraft a = client(mc, chinook);
            shoot(mc, "booth-hover");
            verdict("its rotors turn at speed, seen by the client", () -> a != null && a.rotor() > 0.9f ? null : "rotor " + (a == null ? null : a.rotor()));
            verdict("and it is off the ground", () -> a != null && a.getY() > ground + 4.0 ? null : "height " + (a == null ? null : a.getY() - ground));
        }));
        // --- the Sling Container on its hook --------------------------------------------------------
        s.add(new Step(t += 2, () -> onServer(mc, sp -> withChinook(sp, a -> {
            // Settled in its hover by now (the climb carried it on a little past where it was set):
            // put it seven up again, the hook three over the container's eye.
            a.setPos(a.getX(), ground + 7.0, a.getZ());
            Vec3 hook = a.hookPoint();
            Vehicle c = Vehicle.create(sp.serverLevel(), CONTAINER, new Vec3(hook.x, ground, hook.z), EAST);
            if (!(c instanceof SlungLoad load)) {
                LOG.error("booth: FAIL the Sling Container is a slung load -- {}", c);
                return;
            }
            sp.serverLevel().addFreshEntity(load);
            box = load.getUUID();
        }))));
        s.add(new Step(t += 10, () -> onServer(mc, sp -> withChinook(sp, a -> {
            a.hookKey(sp);
            a.setScriptedFlight(new FlightInput(0, 0, 1, true, false, 0.0));
        }))));
        s.add(new Step(t += 25, () -> onServer(mc, sp -> withChinook(sp, a -> a.setScriptedFlight(new FlightInput(0, 0, 0, true, false, 0.0))))));
        s.add(new Step(t += 40, () -> onServer(mc, sp -> withChinook(sp, a -> aim(sp, middle(a).add(-3.0, -6.0, -22.0), middle(a).add(0.0, -3.0, 0.0))))));
        s.add(new Step(t += SETTLE, () -> {
            SlungLoad load = entity(mc, box) instanceof SlungLoad l ? l : null;
            shoot(mc, "booth-sling");
            verdict("the Sling Container hangs from the hook, off the ground", () -> load != null && load.tower() != null && load.getY() > ground + 1.0
                    ? null : "load " + load + (load == null ? "" : ", tower " + load.tower() + ", height " + (load.getY() - ground)));
        }));
        // --- the crop sprayer over the wheat, flown low by the booth's player ---------------------------
        s.add(new Step(t += 2, () -> onServer(mc, sp -> {
            ServerLevel level = sp.serverLevel();
            for (UUID id : new UUID[] {chinook, box}) {
                if (id != null && level.getEntity(id) instanceof Vehicle old) {
                    old.ejectPassengers();
                    old.discard();
                }
            }
            Vehicle v = Vehicle.create(level, CHINOOK, new Vec3(HX + 4.0, ground, HZ), EAST);
            if (!(v instanceof Aircraft a)) {
                LOG.error("booth: FAIL the Chinook is an aircraft");
                return;
            }
            a.setFuel(a.tank().capacity());
            level.addFreshEntity(a);
            chinook = a.getUUID();
            sp.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(RotorcraftContent.CROP_SPRAYER.get()));
            a.interact(sp, InteractionHand.MAIN_HAND);
            sp.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.BONE_MEAL, 64));
            a.interact(sp, InteractionHand.MAIN_HAND);
            sp.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            sp.getAbilities().flying = false;
            sp.onUpdateAbilities();
            sp.startRiding(a, true);
            a.sprayKey(sp);
        })));
        s.add(new Step(t += 20, () -> {
            mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
            if (mc.player != null) {
                mc.player.setYRot(EAST);
                mc.player.setXRot(18.0f);
            }
            RotorcraftKeys.ASCEND.setDown(true);
        }));
        // The rotor started spooling when the pilot boarded, twenty ticks before; it spools in 80 ticks,
        // so it lifts some 52 ticks into the climb, and a dozen more and the drift take it five up.
        s.add(new Step(t += 64, () -> RotorcraftKeys.ASCEND.setDown(false)));
        s.add(new Step(t += 15, () -> mc.options.keyUp.setDown(true)));
        s.add(new Step(t += 30, () -> mc.options.keyUp.setDown(false)));
        s.add(new Step(t += 8, () -> {
            Aircraft a = client(mc, chinook);
            shoot(mc, "booth-spraying");
            verdict("the sprayer is fitted and spraying", () -> a != null && a.sprayerFitted() && a.spraying() ? null
                    : "fitted " + (a != null && a.sprayerFitted()) + ", spraying " + (a != null && a.spraying()));
            LOG.info("booth: spraying at {} over the ground", a == null ? null : a.getY() - ground);
        }));
        s.add(new Step(t += 50, () -> onServer(mc, sp -> {
            int grown = 0;
            for (int x = 14; x < 34; x++) {
                for (int z = -7; z < 7; z++) {
                    var state = sp.serverLevel().getBlockState(BlockPos.containing(HX + x, ground, HZ + z));
                    if (state.getBlock() instanceof CropBlock crop && crop.getAge(state) > 0) {
                        grown++;
                    }
                }
            }
            int n = grown;
            verdict("the pass grew wheat under the boom", () -> n > 20 ? null : "grown " + n);
        })));
        s.add(new Step(t += 20, () -> {
            mc.options.setCameraType(CameraType.FIRST_PERSON);
            LOG.info("booth: PASS all checks ran");
            phase = Phase.DONE;
            mc.stop();
        }));
        return s;
    }

    /** effects: returns a stand-in player at {@code at}: a server player whose connection goes nowhere, seen by the booth's client as anyone else */
    private static ServerPlayer standIn(ServerPlayer sp, String name, Vec3 at) {
        var server = sp.getServer();
        var cookie = net.minecraft.server.network.CommonListenerCookie.createInitial(new com.mojang.authlib.GameProfile(UUID.randomUUID(), name), false);
        ServerPlayer p = new ServerPlayer(server, sp.serverLevel(), cookie.gameProfile(), cookie.clientInformation());
        var connection = new net.minecraft.network.Connection(net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        new io.netty.channel.embedded.EmbeddedChannel(connection);
        server.getPlayerList().placeNewPlayer(connection, p, cookie);
        p.teleportTo(sp.serverLevel(), at.x, at.y, at.z, 0.0f, 0.0f);
        return p;
    }

    // --- reading the frame -----------------------------------------------

    /** effects: an Army-green pixel in daylight: green over blue, red near green, not bright */
    private static boolean olive(int rgb) {
        int r = rgb >> 16 & 0xFF, g = rgb >> 8 & 0xFF, b = rgb & 0xFF;
        return g > 30 && g < 140 && g > b + 8 && Math.abs(r - g) < 20;
    }

    private static boolean redPaint(int rgb) {
        int r = rgb >> 16 & 0xFF, g = rgb >> 8 & 0xFF, b = rgb & 0xFF;
        return r > 40 && r > g * 1.4 && r > b * 1.3;
    }

    /** effects: returns how many pixels of the frame's middle (rows 15..85 %, columns 10..90 %) satisfy {@code test} */
    private static int count(Minecraft mc, IntPredicate test) {
        try (NativeImage image = Screenshot.takeScreenshot(mc.getMainRenderTarget())) {
            int n = 0;
            int w = image.getWidth(), h = image.getHeight();
            for (int y = (int) (h * .15); y < (int) (h * .85); y++) {
                for (int x = (int) (w * .1); x < (int) (w * .9); x++) {
                    int abgr = image.getPixelRGBA(x, y);
                    int rgb = (abgr & 0xFF) << 16 | (abgr >> 8 & 0xFF) << 8 | (abgr >> 16 & 0xFF);
                    if (test.test(rgb)) {
                        n++;
                    }
                }
            }
            return n;
        }
    }

    // --- plumbing --------------------------------------------------------

    /** effects: returns the client's aircraft of {@code id}, or null */
    @org.jetbrains.annotations.Nullable
    private static Aircraft client(Minecraft mc, UUID id) {
        return entity(mc, id) instanceof Aircraft a ? a : null;
    }

    /** effects: returns the client's entity of {@code id}, or null */
    @org.jetbrains.annotations.Nullable
    private static net.minecraft.world.entity.Entity entity(Minecraft mc, UUID id) {
        if (mc.level == null || id == null) {
            return null;
        }
        for (var e : mc.level.entitiesForRendering()) {
            if (e.getUUID().equals(id)) {
                return e;
            }
        }
        return null;
    }

    private static void onServer(Minecraft mc, Consumer<ServerPlayer> action) {
        MinecraftServer server = mc.getSingleplayerServer();
        if (server == null || mc.player == null) {
            return;
        }
        server.execute(() -> {
            ServerPlayer sp = server.getPlayerList().getPlayer(mc.player.getUUID());
            if (sp != null) {
                action.accept(sp);
            }
        });
    }

    private static void withChinook(ServerPlayer sp, Consumer<Aircraft> action) {
        if (sp.serverLevel().getEntity(chinook) instanceof Aircraft a) {
            action.accept(a);
        } else {
            LOG.error("booth: FAIL the Chinook is in the level -- gone");
        }
    }

    private static void shoot(Minecraft mc, String name) {
        Screenshot.grab(mc.gameDirectory, name + ".png", mc.getMainRenderTarget(),
                message -> LOG.info("booth: {}", message.getString()));
    }

    /** Runs {@code check}; null is a pass, anything else the failure's detail. */
    private static void verdict(String what, Supplier<String> check) {
        String detail;
        try {
            detail = check.get();
        } catch (RuntimeException e) {
            detail = e.toString();
        }
        if (detail == null) {
            LOG.info("booth: PASS {}", what);
        } else {
            LOG.error("booth: FAIL {} -- {}", what, detail);
        }
    }
}
